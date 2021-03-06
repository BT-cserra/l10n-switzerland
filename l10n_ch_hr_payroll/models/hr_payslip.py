# -*- coding: utf-8 -*-
#
#  File: models/hr_payslip.py
#  Module: l10n_ch_hr_payroll
#
#  Created by cyp@open-net.ch
#
#  Copyright (c) 2015-TODAY Open-Net Ltd.
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp import models, fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    # ---------- Fields management

    invoices = fields.One2many('account.invoice', 'slip_id',
                               string='Invoices')
    expenses = fields.One2many('hr.expense.expense', 'slip_id',
                               string='Expenses')
    move_lines = fields.One2many('account.move.line', 'slip_id',
                                 string='Journal Items')

    # ---------- Utilities

    @api.multi
    def compute_sheet(self):

        # First, detach invoices from the pay slips
        InvoiceObj = self.env['account.invoice']
        invoices = InvoiceObj.search([('slip_id', 'in', self.ids)])
        if invoices:
            invoices.write({'slip_id': False})

        # Second, detach expenses from the pay slips
        ExpenseObj = self.env['hr.expense.expense']
        expenses = ExpenseObj.search([('slip_id', 'in', self.ids)])
        if expenses:
            expenses.write({'slip_id': False})

        # Third, detach account move lines from the pay slips
        AccountMoveLineObj = self.env['account.move.line']
        aml = AccountMoveLineObj.search([('slip_id', 'in', self.ids)])
        if aml:
            aml.write({'slip_id': False})

        ret = super(HrPayslip, self).compute_sheet()

        # Then, re-link the invoices, the expenses
        # and the account move lines using the criterias
        InvoiceLineObj = self.env['account.invoice.line']
        for payslip in self:
            # No contract? forget about it
            if not payslip.contract_id:
                continue

            # No user? forget about it
            user_id = payslip.contract_id.employee_id.user_id.id
            if not user_id:
                continue
            employee_id = payslip.contract_id.employee_id.id

            # Look for invoice lines
            inv_ids = []
            filters = [
                ('invoice_id.user_id', '=', user_id),
                ('product_id', '!=', False),
                ('invoice_id.state', 'in', ['open', 'paid']),
                ('invoice_id.type', '=', 'out_invoice'),
            ]
            move_ids = []
            for invl in InvoiceLineObj.search(filters):
                if invl.invoice_id.id not in inv_ids:
                    inv_ids.append(invl.invoice_id.id)
                    invl.invoice_id.write({'slip_id': payslip.id})
                if invl.invoice_id.move_id and \
                        invl.invoice_id.move_id.id not in move_ids:
                    move_ids.append(str(invl.invoice_id.move_id.id))

            inv_lines = InvoiceLineObj.search(filters)
            invoices = inv_lines.mapped('invoice_id')
            invoices.write({'slip_id': payslip.id})
            moves = invoices.mapped('move_id')

            # Look for expenses
            filters = [
                ('employee_id', '=', employee_id),
                ('slip_id', '=', False),
                ('state', '=', ['done', 'accepted']),
            ]
            expenses = ExpenseObj.search(filters)
            if expenses:
                expenses.write({'slip_id': payslip.id})

            # Look for account move lines
            if moves:
                query = """select l3.id
from account_move_line l1, account_move_line l2, account_move_line l3,
account_account a
where l1.move_id in (%s)
and (
(l1.reconcile_id=l2.reconcile_id and l2.reconcile_id != 0)
  or
(l1.reconcile_partial_id=l2.reconcile_partial_id and
 l2.reconcile_partial_id != 0))
and l3.move_id=l2.move_id
and (l3.reconcile_id=0 or l3.reconcile_id is null)
and (l3.reconcile_partial_id=0 or l3.reconcile_partial_id is null)
and l3.account_id=a.id
and (l3.slip_id=0 or l3.slip_id is null)
and a.type='liquidity'""" % ','.join([str(i) for i in moves.ids])

                self.env.cr.execute(query)
                move_line_ids = [str(x[0]) for x in self.env.cr.fetchall()]
                if move_line_ids:
                    q = """update account_move_line
set slip_id=%d where id in (%s)""" % (payslip.id, ','.join(move_line_ids))
                    self.env.cr.execute(q)

        return ret

    def process_sheet(self):
        ExpenseObj = self.env['hr.expense.expense']
        expenses = ExpenseObj.search([
            ('slip_id', '=', self.id)
        ])
        expenses.write({'state': 'done'})
        return super(HrPayslip, self).process_sheet()
