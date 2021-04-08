# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class PortalSession(http.Controller):

    @http.route(['/my/sessions'], type='http', auth="user", website=True)
    def portal_my_sessions(self):
        sessions = request.env['openacademy.session'].search([])
        return request.render("aopenacademy_portal.portal_sessions_list", {
            'sessions': sessions,
            'page_name': 'session',
            'session_count': len(sessions)
        })

    @http.route(['/my/sessions/<int:session_id>'], type='http', auth="user", website=True)
    def portal_my_invoice_detail(self, session_id):
        domain = [('id', '=', session_id)]
        session = request.env['openacademy.session'].search(domain)
        return request.render("aopenacademy_portal.portal_session_details", {
            'session': session,
            'page_name': 'session'
        })

    @http.route(['/my/sessions/<int:session_id>/attendees'], type='http', auth="user", website=True)
    def portal_my_session_attendees(self, session_id):
        domain = ['&', ('instructor_id', '=', request.env.user.partner_id.id), ('id', '=', session_id)]
        session = request.env['openacademy.session'].sudo().search(domain)
        return request.render("aopenacademy_portal.portal_session_attendees", {
            'attendee_session': session,
            'page_name': 'session'
        })