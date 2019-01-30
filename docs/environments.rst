Panhandler Environments
=======================

Often times, it is desirable to store environment specific data outside of a git repository. Panhandler provides
a mechanism to do this using 'Environments'.

What is an Environment
-----------------------

An environment is a collection of secrets that can be loaded and managed as a unit. For example, you may want to keep
all AWS related secrets together in an environment called 'AWS'. When panhandler displays a web form from a configuration
set, any variables from the configuration template that share a name with a secret in the currently loaded environment,
that value will be pre-populated.

This is especially useful, if you have multiple environments such as 'AWS-QA', 'AWS-PROD', and 'AWS-DEV'.


Loading an Environment
-----------------------

To load an environment, click on the 'lock' icon on the right of the navigation bar. You will be presented with
an unlock password. If you have not already created
