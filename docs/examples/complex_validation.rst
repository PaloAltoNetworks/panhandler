.. _`example_complex_validation`:

Example Complex Validation Skillet
===================================

This is a more complex example showing how to validate a portion of a PAN-OS configuration. Often times, you need to
check for specific values or apply some simple logic to a portion of the config to determine if it is considered
compliant or not. Skillets of type `pan_validation` allow you to do just that.

By default, Panhandler will always supply a variable called 'config' that contains the NGFW running config. The `parse`
cmd can be used to pull out and capture specific parts of that config. In this example, we use an advanced `xpath` query
to return a variable containing a list of all file-blocking profiles that have either the desired 'file type' or 'any'
in the member list. We then use the 'filter_items' attribute to further filter the list to only include those items
that have an 'action' of block. In this way, you can find objects in the configuration without knowing the full
XPATH.

The snippets with a cmd type of `validate` is where the actual compliance checks are performed. The `test` attribute
will be evaluated as a jinja boolean expression. True values are considered to have 'passed' this test.


.. code-block:: yaml

    name: complex_validation_323E38BD-D5E0-4ED2-8F39-3AE283B899AD

    label: Complex Validation Example - File Blocking Profiles

    description: |
      This skillet checks the running config to ensure at least one file-blocking profile exists with the desired
      file type and has an action of 'block'.

    type: pan_validation

    labels:
      collection:
        - Example Skillets

    variables:
      - name: file_type
        description: File Type to Check
        default: torrent
        type_hint: text
        help_text: Which type of file to check to ensure it is being blocked correctly

    snippets:
      - name: profile_objects
        cmd: parse
        variable: config
        outputs:
          # This example uses a complex XPATH query to find a list of all file-blocking profile entries that have
          # either the desired file-type as a member or 'any'
          - name: fb_profiles
            capture_object: |
              /config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/file-blocking//
              entry/rules/entry/file-type/member[text()="{{ file_type }}" or text()="any"]/../..
            # This further filters the list to *only* include those items that have an action of 'block'
            filter_items: item | element_value('entry.action') == 'block'

      - name: file_blocking_check
        label: Ensure at least one file blocking profile is blocking {{ file_type }}
        test: |
          (
          fb_profiles | length
          )
        documentation_link: https://ironscotch.readthedocs.io/en/docs_dev/viz_guide_panos.html#object-security-profiles-antivirus-blocking
