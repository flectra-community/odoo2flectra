# {{ project_title }}

{{ project_intro }}

{% if modules %}

Available addons
----------------

addon | version | summary
--- | --- | ---
{% for key, mod in modules.items() -%}
[{{ key }}]({{ key }}/) | {{ mod['version'] }}| {{ ('summary' in mod and mod['summary'] or 'name' in mod and mod['name'] or '').replace('\n','').replace('\r','') }}
{% endfor %}

{% endif %}