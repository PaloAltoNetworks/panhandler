.. _`example_when`:

Example Skillet with When Conditionals
=======================================

This is a basic 'validation' Skillet example that uses 'when' conditionals to 'skip' certain snippets. This can be
useful to perhaps skip validation tests that are not relevant. For example, there is not need to test a sub-element's
value if the parent element does not exist.


.meta-cnc.yaml
--------------

.. code-block:: yaml

    #
    # Example When Conditional
    #
    # In order to properly validate a config, it is often necessary to convert the XML structure to an object, which
    # can then be used in jinja expression to perform basic logic and validation. These examples demonstrate how
    # skillets are optimized for this task.
    #

    name: example-when-conditional
    label: Example of how to use 'when' conditional

    description: |
      This example Skillet shows how to parse and validate a config using the 'when' conditionals.
      This is useful when you want to test a portion on a configuration, but only 'when' a pre-condition test passes. In
      this example, we will ensure the statistics-service is enabled, but only 'when' the update-schedule element is
      present and defined.

    type: pan_validation

    labels:
      collection:
        - Example Skillets

    variables:
      - name: SOME_VARIABLE
        description: Some VARIABLE
        default: present
        type_hint: text

    snippets:
      - name: show_device_system
        cmd: parse
        variable: config
        outputs:
          - name: update_schedule_object
            capture_object: /config/devices/entry[@name='localhost.localdomain']/deviceconfig/system/update-schedule

      - name: update_schedule_configured
        label: Ensure Update Schedules are Configured
        test: update_schedule_object is not none
        documentation_link: https://docs.paloaltonetworks.com/pan-os/8-0/pan-os-new-features/content-inspection-features/telemetry-and-threat-intelligence-sharing

      - name: update_schedule_stats_service_configured
        when: update_schedule_object is not none
        label: Ensure Statistics Service is enabled
        test: update_schedule_object| tag_present('update-schedule.statistics-service')
        documentation_link: https://docs.paloaltonetworks.com/pan-os/8-0/pan-os-new-features/content-inspection-features/telemetry-and-threat-intelligence-sharing

