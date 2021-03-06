#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2010-2012 Associazione OpenERP Italia
#    (<http://www.openerp-italia.org>).
#    Copyright(c)2008-2010 SIA "KN dati".(http://kndati.lv) All Rights Reserved.
#                    General contacts <info@kndati.lv>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import os
import sys
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP,
    float_compare)


_logger = logging.getLogger(__name__)


class ProductProduct(orm.Model):
    """ Model name: Extra data for product
    """

    _inherit = 'product.product'

    _columns = {
        'is_pallet': fields.boolean(
            'E\' un Pallet',
            help='Utilizzato per calcolare i totali pallet dove occorre'),
        'not_intra_cee_report': fields.boolean(
            'Non in intra CEE',
            help='Non utilizzare l\'articolo nella pagina extra Intra CEE')
    }


class AccountFiscalPosition(orm.Model):
    """ Model name: Extra data for fiscal position
    """

    _inherit = 'account.fiscal.position'

    _columns = {
        'intra_cee_page': fields.boolean(
            'Pagina Intra CEE',
            help='Richiesta la pagina Intra CEE in fattura'),
    }


class ResCompany(orm.Model):
    """ Model name: Privacy policy
    """

    _inherit = 'res.company'

    _columns = {
        'privacy_policy': fields.text('Privacy policy', translate=True),
        }


class ResPartner(orm.Model):
    """ Model name: Privacy policy
    """

    _inherit = 'res.partner'

    _columns = {
        'privacy_policy_signed': fields.boolean('Privacy policy firmata'),
        }


class AccountInvoice(orm.Model):
    """ Model name: AccountInvoice
    """

    _inherit = 'account.invoice'

    def get_invoice_text_mail(self, cr, uid, ids, fields, args, context=None):
        """ Prepare text block for mail depend on customer:
        """
        res = {}
        if len(ids) > 1:
            return res

        invoice_pool = self.pool.get('account.invoice')
        invoice = invoice_pool.browse (cr, uid, ids, context=context)[0]

        if invoice.partner_id.is_private:
            res[ids[0]] = '''Fiscalmente valida come originale ai sensi della 
                Ris. Min. 132/e del 28/05/1997'''
        elif (invoice.partner_id.vat or '').upper().startswith('IT'):
            res[ids[0]] = 'Non valida ai fini fiscali.'
        else:
            res[ids[0]] = '''Fiscally valid as original according to the the 
                Ris. Min. 132/e of 28/05/1997.'''
        return res

    # Override function for report (button click)
    @api.multi
    def invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        assert len(self) == 1, 'Use only for a single id at a time.'
        self.sent = True
        return self.env['report'].get_action(
            self, 'custom_mx_invoice_report')

    _columns = {
        'mail_invoice_text': fields.function(
            get_invoice_text_mail, method=True,
            type='text', string='Mail text', store=False),
        }
