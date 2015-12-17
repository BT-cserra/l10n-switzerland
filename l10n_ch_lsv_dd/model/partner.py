# b-*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 brain-tec AG (http://www.braintec-group.com)
#    All Right Reserved
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
from openerp import models, fields


class ResPartner(models.Model):
    ''' Overrides it so that the res.partner can select which account he/she
        wants to use for LSV or DD payments.
    '''

    _inherit = 'res.partner'

    def get_top_parent(self):
        ''' Returns the top parent of a parent hierarchy.
        '''
        top_parent = self
        while top_parent.parent_id:
            top_parent = top_parent.parent_id
        return top_parent

    lsv_bank_account_id = fields.Many2one('res.partner.bank', 'Bank for LSV',
                                          help='The bank account to use '
                                               'for LSV payment files.')

    dd_bank_account_id = fields.Many2one('res.partner.bank', 'Bank for DD',
                                         help='The bank account to use for DD '
                                              'payment files.')
