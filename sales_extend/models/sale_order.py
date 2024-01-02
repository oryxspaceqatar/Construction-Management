from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class SaleOrders(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('gm_approved', 'GM Approved'),
        ('accounts_approved', 'Accounts Approved'),
        ('md_approved', 'MD Approved'),
        ('sent', "Quotation Sent"),
        ('sale', "Sales Order"),
        ('cancel', "Cancelled"),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    def _can_be_confirmed(self):
        self.ensure_one()
        return self.state in {'draft', 'sent','gm_approved','accounts_approved','md_approved'}

    def general_manager_approve(self):
        template_id = self.env.ref("sales_extend.email_template_edi_sale_approve")
        group_obj = self.env.ref("sales_extend.group_sale_accounts_all_leads")
        emails = list(set(group_obj.users.mapped("login")))
        if template_id and emails:
            emails = ','.join(emails)
            template_id.sudo().with_context({'to_emails': emails}).send_mail(self.id)
            self.write({'state': 'gm_approved'})
        else:
            raise ValidationError("Please assign users to 'Accounts' group for approve.")


    def accounts_approve(self):
        template_id = self.env.ref("sales_extend.email_template_edi_sale_approve")
        group_obj = self.env.ref("sales_extend.group_sale_accounts_all_leads")
        emails = list(set(group_obj.users.mapped("login")))
        if template_id and emails:
            emails = ','.join(emails)
            template_id.sudo().with_context({'to_emails': emails}).send_mail(self.id)
            self.write({'state': 'accounts_approved'})
        else:
            raise ValidationError("Please assign users to 'Accounts' group for approve.")


    def md_approve(self):
        self.write({'state': 'md_approved'})
        template_id = self.env.ref("sales_extend.email_template_edi_sale_approve")
        group_obj = self.env.ref("sales_extend.group_sale_salesman")
        emails = list(set(group_obj.users.mapped("login")))
        if template_id and emails:
            emails = ','.join(emails)
            template_id.sudo().with_context({'to_emails': emails}).send_mail(self.id)
        else:
            raise ValidationError("Please assign users to 'Accounts' group for approve.")

    @api.model
    def create(self,vals):
        res = super().create(vals)
        if res:
            template_id = self.env.ref("sales_extend.email_template_edi_sale_approve")
            group_obj = self.env.ref("sales_team.group_sale_salesman_all_leads")
            emails = list(set(group_obj.users.mapped("login")))
            if template_id and emails:
                emails = ','.join(emails)
                template_id.sudo().with_context({'to_emails': emails}).send_mail(res.id)
            else:
                raise ValidationError("Please assign users to 'Choices GM' group for approve.")
        return res

    def action_confirm(self):
        if self.state != 'md_approved':
            raise ValidationError("You cannot Confirm this order without approval.")
        res = super().action_confirm()
        return res


    # def _find_mail_template(self, force_confirmation_template=False):
    #     self.ensure_one()
    #     template_id = False
    #
    #     if force_confirmation_template or (self.state == 'sale' and not self.env.context.get('proforma', False)):
    #         template_id = int(self.env['ir.config_parameter'].sudo().get_param('sale.default_confirmation_template'))
    #         template_id = self.env['mail.template'].search([('id', '=', template_id)]).id
    #         if not template_id:
    #             template_id = self.env['ir.model.data']._xmlid_to_res_id('sale.mail_template_sale_confirmation',
    #                                                                      raise_if_not_found=False)
    #     if not template_id:
    #         template_id = self.env['ir.model.data']._xmlid_to_res_id('sales_extend.email_template_edi_sale_extend',
    #                                                                  raise_if_not_found=False)
    #
    #     return template_id
