from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import logging

class AccountMove(models.Model):
    _inherit = 'account.move'

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('gm_approved', 'GM Approved'),
            ('procurement_approved', 'Procurement Approved'),
            ('md_approved', 'MD Approved'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default='draft',
    )

    def general_manager_approve(self):
        template_id = self.env.ref("sales_extend.email_template_edi_invoice_approval")
        group_obj = self.env.ref("sales_extend.group_account_invoice_procurement")
        emails = list(set(group_obj.users.mapped("login")))
        if template_id and emails:
            emails = ','.join(emails)
            template_id.sudo().with_context({'to_emails': emails}).send_mail(self.id)
            self.write({'state': 'gm_approved'})
        else:
            raise ValidationError("Please assign users to 'Procurement' group for approve.")

    def procurement_approve(self):
        template_id = self.env.ref("sales_extend.email_template_edi_invoice_approval")
        group_obj = self.env.ref("sales_extend.group_account_invoice_md")
        group_obj2 = self.env.ref("sales_extend.group_account_invoice_accounts_group")
        emails = group_obj.users.mapped("login")
        group2_emails = group_obj2.users.mapped("login")
        emails.extend(group2_emails)
        emails = list(set(emails))
        if template_id and emails:
            emails = ','.join(emails)
            template_id.sudo().with_context({'to_emails': emails}).send_mail(self.id)
            self.write({'state': 'procurement_approved'})
        else:
            raise ValidationError("Please assign users to 'Accounts or MD' group for approve.")

    def md_approve(self):
        self.write({'state': 'md_approved'})

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res and res.move_type == 'out_invoice':
            template_id = self.env.ref("sales_extend.email_template_edi_invoice_approval")
            group_obj = self.env.ref("construction_management.group_requisition_department_manager")
            emails = list(set(group_obj.users.mapped("login")))
            if template_id and emails:
                emails = ','.join(emails)
                template_id.sudo().with_context({'to_emails': emails}).send_mail(res.id)
            else:
                raise ValidationError("Please assign users to 'Choices GM' group for approve.")
        return res

    def action_post(self):
        if self.state != 'md_approved' and self.move_type == 'out_invoice':
            raise ValidationError("You cannot Confirm this Invoice without approval.")
        res = super().action_post()
        return res