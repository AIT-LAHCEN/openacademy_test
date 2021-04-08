# -*- coding: utf-8 -*-

from odoo import fields, models, _


class Partner(models.Model):
    _inherit = 'res.partner'

    # Add a new column to the res.partner model, by default partners are not
    # instructors
    instructor = fields.Boolean("Instructor", default=False)
    session_ids = fields.Many2many('openacademy.session', string="Attended Sessions", readonly=True)

    def list_courses(self):
        return {
            'name': _('Courses'),
            'domain': [],
            #'domain': [('instructor_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'openacademy.course',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def list_sessions(self):
        return {
            'name': _('Sessions'),
            'domain': [('instructor_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'openacademy.session',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }
