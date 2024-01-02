from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('gm_approved', 'GM Approved'),
        ('procurement_approved', 'Procurement Approved'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, tracking=True,
        help=" * Draft: The transfer is not confirmed yet. Reservation doesn't apply.\n"
             " * Waiting another operation: This transfer is waiting for another operation before being ready.\n"
             " * Waiting: The transfer is waiting for the availability of some products.\n(a) The shipping policy is \"As soon as possible\": no product could be reserved.\n(b) The shipping policy is \"When all products are ready\": not all the products could be reserved.\n"
             " * Ready: The transfer is ready to be processed.\n(a) The shipping policy is \"As soon as possible\": at least one product has been reserved.\n(b) The shipping policy is \"When all products are ready\": all product have been reserved.\n"
             " * Done: The transfer has been processed.\n"
             " * Cancelled: The transfer has been cancelled.")

    def general_manager_approve(self):
        template_id = self.env.ref("sales_extend.mail_template_data_delivery_confirmation_approval")
        group_obj = self.env.ref("sales_extend.group_requisition_department_procurement")
        emails = list(set(group_obj.users.mapped("login")))
        if template_id and emails:
            emails = ','.join(emails)
            template_id.sudo().with_context({'to_emails': emails}).send_mail(self.id)
            self.write({'state': 'gm_approved'})
        else:
            raise ValidationError("Please assign users to 'Procurement' group for approve.")

    def procurement_approve(self):
        self.write({'state': 'procurement_approved'})
        # template_id = self.env.ref("sales_extend.mail_template_data_delivery_confirmation_approval")
        # group_obj = self.env.ref("sales_extend.group_requisition_department_md")
        # group_obj2 = self.env.ref("sales_extend.group_requisition_department_accounts")
        # emails = group_obj.users.mapped("login")
        # group2_emails = group_obj2.users.mapped("login")
        # emails.extend(group2_emails)
        # if template_id and emails:
        #     emails = ','.join(emails)
        #     template_id.sudo().with_context({'to_emails': emails}).send_mail(self.id)
        #     self.write({'state': 'procurement_approved'})
        # else:
        #     raise ValidationError("Please assign users to 'Accounts or MD' group for approve.")

    def md_approve(self):
        self.write({'state': 'md_approved'})

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res:
            template_id = self.env.ref("sales_extend.mail_template_data_delivery_confirmation_approval")
            group_obj = self.env.ref("sales_extend.group_account_invoice_gm")
            emails = list(set(group_obj.users.mapped("login")))
            if template_id and emails:
                emails = ','.join(emails)
                template_id.sudo().with_context({'to_emails': emails}).send_mail(res.id)
            else:
                raise ValidationError("Please assign users to 'Choices GM' group for approve.")
        return res