from flask import flash, render_template, request, redirect, url_for

from app import app
from app.forms import InputForm
from migrator import LocalMigrator, CONFIG_DIR


@app.route('/')
def config():
    output = ''
    cisco_output = ''

    input_form = InputForm(data=request.args)

    action = request.args.get('action')

    if action == 'generate_config':
        if input_form.validate():

            hostname = input_form.hostname.data
            interface = input_form.interface.data
            outer_tag = str(input_form.outer_tag.data)

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

    return render_template('config.html', form=input_form, output=output, cisco_output=cisco_output)
