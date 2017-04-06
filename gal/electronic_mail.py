#This file is part of trytontasks_gal. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import yaml
from trytond.pool import Pool
from trytond.transaction import Transaction

def get_templates():
    config = yaml.load(open('tasks/gal/electronic_mail.yml', 'r').read())
    config.setdefault('templates', [])
    return config

def load_lang_tpl(lang, template):
    tpl_dir = 'tasks/gal/electronic_mail'

    name = open(tpl_dir+'/'+template['name']+'_'+lang+'.txt', 'r').read()[:-1]
    subject = open(tpl_dir+'/'+template['subject']+'_'+lang+'.txt', 'r').read()[:-1]
    plain = open(tpl_dir+'/'+template['plain']+'_'+lang+'.txt', 'r').read()[:-1]
    html = open(tpl_dir+'/'+template['html']+'_'+lang+'.txt', 'r').read()[:-1]
    return name, subject, plain, html

def create_email_templates():
    pool = Pool()
    Template = pool.get('electronic.mail.template')
    Model = pool.get('ir.model')
    Report = pool.get('ir.action.report')
    Lang = pool.get('ir.lang')

    models = dict((m.model, m) for m in Model.search([]))
    reports = dict((r.model, r) for r in Report.search([]))
    langs = Lang.search([
            ('code', 'in', ['ca', 'es']),
            ])

    to_filename = []
    for template in get_templates().get('templates', []):
        model = template['model']
        name, subject, plain, html = load_lang_tpl('en', template)

        etemplate = Template()
        etemplate.name = name
        etemplate.model = models.get(model)
        etemplate.from_ = template['from_']
        etemplate.to = template['to']
        etemplate.subject = subject
        etemplate.language = template['language']
        etemplate.plain = plain
        etemplate.html = html
        etemplate.engine = template['engine']
        etemplate.signature = bool(template['signature'])

        if template.get('report') and reports.get(model):
            report = reports.get(model)
            Report.write([report], {'email_filename': template['report']})
            etemplate.reports = [report]
        etemplate.save()

        for lang in langs:
            name, subject, plain, html = load_lang_tpl(lang.code, template)
            etemplate.name = name
            etemplate.subject = subject
            etemplate.plain = plain
            etemplate.html = html

            with Transaction().set_context(language=lang.code):
                Template.write([etemplate], etemplate._save_values)
