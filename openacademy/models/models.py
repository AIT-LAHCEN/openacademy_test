# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import models, fields, api, exceptions, _, tools


class Course(models.Model):
    _name = 'openacademy.course'
    _description = "OpenAcademy Courses"

    name = fields.Char(string="Title", required=True)
    description = fields.Text()
    responsible_id = fields.Many2one('res.users', ondelete='set null', string="Responsible", index=True)
    session_ids = fields.One2many('openacademy.session', 'course_id', string="Sessions")
    totalPrice = fields.Float(digits=(10, 2), help="Course Sessions price", compute="get_total_price")
    session_count = fields.Integer(compute='_session_counting')
    invoiced = fields.Boolean("Invoiced", default=False)

    def list_session(self):
        return {
            'name': _('Sessions'),
            'domain': [('course_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'openacademy.session',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def list_invoices(self):
        return {
            'name': _('Invoices'),
            'domain': [('ref', '=', self.name)],
            'view_type': 'form',
            'res_model': 'account.move',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def invoicing_sessions(self):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            #'partner_id': self.session_ids.instructor_id,
            'date': fields.Date.today(),
            'ref': self.name,
            'invoice_line_ids': [(0, 0, {
                #'product_id': self.env['openacademy.course'].create({'name': self.name}),
                'quantity': 1,
                'name': self.name,
                'price_unit': self.totalPrice,
            })]
        })
        #invoice.action_post()
        self.invoiced = True
        return invoice

    @api.depends('session_ids')
    def get_total_price(self):
        for r in self:
            tot = 0
            sessions = r.session_ids
            for s in sessions:
                tot += s.price
            r.totalPrice = tot

    @api.depends('session_ids')
    def _session_counting(self):
        for r in self:
            r.session_count = len(r.session_ids)

    _sql_constraints = [
        ('name_description_check',
         'CHECK(name != description)',
         "The title of the course should not be the description"),

        ('name_unique',
         'UNIQUE(name)',
         "The course title must be unique"),
    ]

    def copy(self, default=None):
        default = dict(default or {})
        copied_count = self.search_count(
            [('name', '=like', _(u"Copy of {}%").format(self.name))])
        if not copied_count:
            new_name = _(u"Copy of {}").format(self.name)
        else:
            new_name = _(u"Copy of {} ({})").format(self.name, copied_count)
        default['name'] = new_name
        return super(Course, self).copy(default)


class Session(models.Model):
    _name = 'openacademy.session'
    _description = "OpenAcademy Sessions"

    name = fields.Char(required=True)
    start_date = fields.Date(default=fields.Date.today)
    duration = fields.Float(digits=(6, 2), help="Duration in days")
    seats = fields.Integer(string="Number of seats")
    active = fields.Boolean(default=True)
    color = fields.Integer()
    instructor_id = fields.Many2one('res.partner', string="Instructor",
                                    domain=[('instructor', '=', True), ('category_id.name', 'ilike', "Teacher")])
    course_id = fields.Many2one('openacademy.course', ondelete='cascade', string="Course")#, required=True)
    attendee_ids = fields.Many2many('res.partner', string="Attendees")
    taken_seats = fields.Float(string="Taken seats", compute='_taken_seats')
    end_date = fields.Date(string="End Date", store=True, compute='_get_end_date', inverse='_set_end_date')
    attendees_count = fields.Integer(string="Attendees count", compute='_get_attendees_count', store=True)
    price = fields.Float(digits=(10,2), help="Session price")
    invoiced = fields.Boolean("Invoiced", default=False)

    def list_session_invoices(self):
        return {
            'name': _('Invoices'),
            'domain': [('ref', '=', self.name)],
            'view_type': 'tree',
            'res_model': 'account.move',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def invoicing_session(self):
        attendeesInvoices = self.env['account.move'].create([{
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'partner_id': self.attendee_ids[i],
            'date': fields.Date.today(),
            'ref':self.name,
            'invoice_line_ids': [(0, 0, {
                #'product_id': self.id,
                'quantity': 1,
                'name': self.name,
                'price_unit': self.price,
            })]
        } for i in range(len(self.attendee_ids))])
        instructorInvoice = self.env['account.move'].create([{
                'move_type': 'in_invoice',
                'invoice_date': fields.Date.today(),
                'partner_id': self.instructor_id,
                'date': fields.Date.today(),
                'ref': self.name,
                'invoice_line_ids': [(0, 0, {
                    # 'product_id': self.id,
                    'quantity': 1,
                    'name': self.name,
                    'price_unit': self.price,
                })]
            }
        ])
        attendeesInvoices.action_post()
        instructorInvoice.action_post()
        self.invoiced = True

    def launch_session_wizard(self):
        return {
            'name': _('Add Attendees'),
            'domain': [],
            'view_type': 'form',
            'res_model': 'openacademy.wizard',
            'view_id': False,
            'view_mode': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    @api.depends('seats', 'attendee_ids')
    def _taken_seats(self):
        for r in self:
            if not r.seats:
                r.taken_seats = 0.0
            else:
                r.taken_seats = 100.0 * len(r.attendee_ids) / r.seats

    @api.onchange('seats', 'attendee_ids')
    def _verify_valid_seats(self):
        if self.seats < 0:
            return {
                'warning': {
                    'title': _("Incorrect 'seats' value"),
                    'message': _("The number of available seats may not be negative"),
                },
            }
        if self.seats < len(self.attendee_ids):
            return {
                'warning': {
                    'title': _("Too many attendees"),
                    'message': _("Increase seats or remove excess attendees"),
                },
            }

    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        for r in self:
            if not (r.start_date and r.duration):
                r.end_date = r.start_date
                continue

            # Add duration to start_date, but: Monday + 5 days = Saturday, so
            # subtract one second to get on Friday instead
            duration = timedelta(days=r.duration, seconds=-1)
            r.end_date = r.start_date + duration

    def _set_end_date(self):
        for r in self:
            if not (r.start_date and r.end_date):
                continue

            # Compute the difference between dates, but: Friday - Monday = 4 days,
            # so add one day to get 5 days instead
            r.duration = (r.end_date - r.start_date).days + 1

    @api.depends('attendee_ids')
    def _get_attendees_count(self):
        for r in self:
            r.attendees_count = len(r.attendee_ids)

    @api.constrains('instructor_id', 'attendee_ids')
    def _check_instructor_not_in_attendees(self):
        for r in self:
            if r.instructor_id and r.instructor_id in r.attendee_ids:
                raise exceptions.ValidationError(_("A session's instructor can't be an attendee"))


class PivotReporting(models.Model):
    _name = 'openacademy.pivot.report'
    _auto = False
    _description = 'Openacademy pivot reporting'
    _rec_name = 'id'

    #create_date = fields.Datetime('Creation date', readonly=True)
    #id = fields.Many2one('openacademy.course', string="Course", readonly=True)
    #session_ids = fields.Many2one('openacademy.session', string="Sessions")
    #instructor_id = fields.Many2one('res.partner', string="Instructor",
    #                                domain=[('instructor', '=', True), ('category_id.name', 'ilike', "Teacher")])
    name = fields.Char('Title')
    session_per_course = fields.Integer(string="Number of Session per Course", readonly=True)
    creation_date = fields.Datetime('Creation Date', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT c.id, c.name, count(s.id) AS session_per_course, c.create_date AS creation_date
                FROM openacademy_course AS c
                JOIN openacademy_session AS s ON c.id = s.course_id
                GROUP BY c.id
            )
        """ % self._table)
