from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    state = fields.Selection([
        ('draft', 'RFQ'),
        ('gm_approved', 'GM Approved'),
        ('md_approved', 'MD Approved'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)

    def general_manager_approve(self):
        template_id = self.env.ref("sales_extend.email_template_edi_purchase_approval")
        group_obj = self.env.ref("sales_extend.group_purchase_md")
        group_obj2 = self.env.ref("sales_extend.group_requisition_department_accounts")
        emails = group_obj.users.mapped("login")
        group2_emails = group_obj2.users.mapped("login")
        emails.extend(group2_emails)
        emails = list(set(emails))
        if template_id and emails:
            emails = ','.join(emails)
            template_id.sudo().with_context({'to_emails': emails}).send_mail(self.id)
            self.write({'state': 'gm_approved'})
        else:
            raise ValidationError("Please assign users to 'Accounts or MD' group for approve.")

    def md_approve(self):
        self.write({'state': 'md_approved'})

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res:
            template_id = self.env.ref("sales_extend.email_template_edi_purchase_approval")
            group_obj = self.env.ref("sales_extend.group_purchase_gm")
            emails = list(set(group_obj.users.mapped("login")))
            if template_id and emails:
                emails = ','.join(emails)
                template_id.sudo().with_context({'to_emails': emails}).send_mail(res.id)
            else:
                raise ValidationError("Please assign users to 'Choices GM' group for approve.")
        return res

    def button_confirm(self):
        for order in self:
            if order.state not in ['gm_approved', 'md_approved']:
                continue
            order.order_line._validate_analytic_distribution()
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True