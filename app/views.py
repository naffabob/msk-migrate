from flask import flash, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

from app import app
from app.forms import InputForm, ConfigForm, HostnameForm
from migrator import LocalMigrator, CONFIG_DIR


@app.route('/migrate/')
def config():
    page = 'config'

    output = ''
    cisco_output = ''

    input_form = InputForm(data=request.args)

    action = request.args.get('action')

    if action == 'generate_config':
        if input_form.validate():

            hostname = input_form.hostname.data
            interface = input_form.interface.data
            outer_tag = input_form.outer_tag.data

            try:
                with open(f'{CONFIG_DIR}{hostname}') as f:
                    dev_config = f.read()
            except FileNotFoundError:
                flash('No such config file.', category='error')
                return redirect(url_for('config'))

            lm = LocalMigrator(dev_config)
            output += lm.config_ip_ifaces(interface, outer_tag)
            output += lm.config_unnumbered_ifaces(interface, outer_tag)
            output += lm.config_static_subscribers(interface, outer_tag)

            if not output:
                flash(f'No current active interfaces for outer: {interface}.{outer_tag}', category='danger')

            cisco_output += lm.config_cisco_shutdown(interface, outer_tag)

    return render_template('config.html', form=input_form, page=page, output=output, cisco_output=cisco_output)


@app.route('/migrate/upload', methods=['GET', 'POST'])
def upload():
    page = 'upload'

    form = ConfigForm()
    action = request.form.get('action')

    if request.method == 'POST' and action == 'upload':
        if form.validate_on_submit():
            f = form.config.data
            filename = secure_filename(f.filename)
            f.save(f'{CONFIG_DIR}{filename}')

            flash(f'File {filename} successfully uploaded', category='success')
            return redirect(url_for('config'))

    return render_template('upload.html', form=form, page=page)


@app.route('/migrate/stats')
def stats():
    page = 'stats'

    form = HostnameForm(data=request.args)

    action = request.args.get('action')

    if action == 'get_stats':
        if form.validate():
            hostname = form.hostname.data
            try:
                with open(f'{CONFIG_DIR}{hostname}') as f:
                    dev_config = f.read()
            except FileNotFoundError:
                flash('No such config file.', category='error')
                return redirect(url_for('stats'))

            lm = LocalMigrator(dev_config)
            ifaces = lm.get_statistics()
        return render_template('stats.html', form=form, page=page, ifaces=ifaces)

    return render_template('stats.html', form=form, page=page)
