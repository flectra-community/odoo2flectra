Odoo to Flectra Repository Converter
====================================

Convert your repository containing multiple odoo modules to flectra.

Usage
-----

### Easiest way
  
If you are using docker you can follow these steps to migrate your repository:

1. Create a base folder for conversion

        mkdir -p /tmp/convert
        
2. Clone your odoo repository into folder called odoo

        git clone https://github.com/jamotion/sale-workflow.git /tmp/convert/odoo

3. Start Conversion with following command:

        docker run --rm -ti -v /tmp/convert:/opt/migrator/data flecom/odoo2flectra --name "Sale Workflow"
        
4. When conversion is finished, you will find the converted repository in folder /tmp/convert/flectra

        ls /tmp/convert/flectra
        
### Manual way

If you do not use docker (why not!?!), it is possible to run the python script manually.
For this python > 3.5 and jinja package are required.

1. Clone this repository with:

        git clone https://gitlab.com/flectra-community/devops/odoo-2-flectra-converter.git
        cd odoo-2-flectra-converter
        chmod +x migrate_repository.py
        
2. Clone your odoo repository into folder called odoo

        git clone https://github.com/jamotion/sale-workflow.git ./odoo

3. Start Conversion with following command:

        ./migrate_repository --name "Sale Workflow"
        
4. When conversion is finished, you will find the converted repository in folder ./flectra

        ls ./flectra
        
### Command line parameters

* **--name**: Set the name of the repository, used for generated README file
(required) 
* **--company**: Set the name of your company, used on multiple places
(optional, default "Jamotion GmbH") 
* **--contributor**: Set your name (e.g. "Renzo Meister, Jamotion <rm@jamotion.ch>")
(optional, default "Jamotion <info@jamotion.ch>")
* **--src**: Source path of your odoo repository
(optional, default "./odoo")
* **--dest**: Destination path where the converted repository will be stored
(optional, default "./flectra")
* **--debug**: Use DEBUG as loglevel
(optional)


#### Full example with docker

        docker run --rm -ti \
                   -v /tmp/convert:/opt/migrator/data \
                   flecom/odoo2flectra \
                   --name "Sale Workflow" \
                   --company "Flectra Community" \
                   --contributor "Flectra Community <info@flectra-community.org>" \
                   --src "./sale-workflow" \
                   --dest "./flectra/sale-workflow" \
                   --debug

#### Full example with direct call

        ./migrate_repository --name "Sale Workflow" \
                   --company "Flectra Community" \
                   --contributor "Flectra Community <info@flectra-community.org>" \
                   --src "./sale-workflow" \
                   --dest "./flectra/sale-workflow" \
                   --debug
