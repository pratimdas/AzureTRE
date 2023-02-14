import copy
from models.domain.resource_template import PipelineStep, PipelineStepProperty
from service_bus.substitutions import substitute_properties, substitute_value


def test_substitution_for_primary_resource(primary_resource):
    resource_dict = primary_resource.dict()

    # single array val
    val_to_sub = "{{ resource.properties.address_prefix }}"
    val = substitute_value(val_to_sub, resource_dict, None, None)
    assert val == ["172.0.0.1", "192.168.0.1"]

    # array val to inject, with text. Text will be dropped.
    val_to_sub = "{{ resource.properties.fqdn }} - this text will be removed because fqdn is a list and shouldn't be concatenated into a string"
    val = substitute_value(val_to_sub, resource_dict, None, None)
    assert val == ["*pypi.org", "files.pythonhosted.org", "security.ubuntu.com"]

    # single string val, with text. Will be concatenated into text.
    val_to_sub = "I think {{ resource.templateName }} is the best template!"
    val = substitute_value(val_to_sub, resource_dict, None, None)
    assert val == "I think template name is the best template!"

    # multiple string vals, with text. Will be concatenated.
    val_to_sub = "I think {{ resource.templateName }} is the best template, and {{ resource.templateVersion }} is a good version!"
    val = substitute_value(val_to_sub, resource_dict, None, None)
    assert val == "I think template name is the best template, and 7 is a good version!"


def test_substitution_for_primary_resource_parents(primary_resource, resource_ws_parent, resource_ws_svc_parent):
    primary_resource_dict = primary_resource.dict()
    parent_ws_resource_dict = resource_ws_parent.dict()
    parent_ws_svc_resource_dict = resource_ws_svc_parent.dict()

    # ws parent
    # single array val
    val_to_sub = "{{ parent_workspace.properties.address_prefix }}"
    val = substitute_value(val_to_sub, None, parent_ws_resource_dict, None)
    assert val == ["172.1.1.1", "192.168.1.1"]

    # array val to inject, with text. Text will be dropped.
    val_to_sub = "{{ parent_workspace.properties.fqdn }} - this text will be removed because fqdn is a list and shouldn't be concatenated into a string"
    val = substitute_value(val_to_sub, None, parent_ws_resource_dict, None)
    assert val == ["*pypi.org", "security.ubuntu.com"]

    # single string val, with text. Will be concatenated into text.
    val_to_sub = "I think {{ parent_workspace.templateName }} is the best template!"
    val = substitute_value(val_to_sub, None, parent_ws_resource_dict, None)
    assert val == "I think ws template name is the best template!"

    # multiple string vals, with text. Will be concatenated.
    val_to_sub = "I think {{ parent_workspace.templateName }} is the best template, and {{ parent_workspace.templateVersion }} is a good version!"
    val = substitute_value(val_to_sub, None, parent_ws_resource_dict, None)
    assert val == "I think ws template name is the best template, and 8 is a good version!"

    # ws svc parent
    # single array val
    val_to_sub = "{{ parent_workspace_service.properties.address_prefix }}"
    val = substitute_value(val_to_sub, None, None, parent_ws_svc_resource_dict)
    assert val == ["172.2.2.2", "192.168.2.2"]

    # array val to inject, with text. Text will be dropped.
    val_to_sub = "{{ parent_workspace_service.properties.fqdn }} - this text will be removed because fqdn is a list and shouldn't be concatenated into a string"
    val = substitute_value(val_to_sub, None, None, parent_ws_svc_resource_dict)
    assert val == ["*pypi.org", "files.pythonhosted.org"]

    # single string val, with text. Will be concatenated into text.
    val_to_sub = "I think {{ parent_workspace_service.templateName }} is the best template!"
    val = substitute_value(val_to_sub, None, None, parent_ws_svc_resource_dict)
    assert val == "I think svc template name is the best template!"

    # multiple string vals, with text. Will be concatenated.
    val_to_sub = "I think {{ parent_workspace_service.templateName }} is the best template, and {{ parent_workspace_service.templateVersion }} is a good version!"
    val = substitute_value(val_to_sub, None, None, parent_ws_svc_resource_dict)
    assert val == "I think svc template name is the best template, and 9 is a good version!"

    # multiple sources (primary + both parents) multiple string vals, with text. Will be concatenated.
    val_to_sub = "I am the primary resource ( a user resource - {{ resource.properties.display_name }}), my workspace parent is {{ parent_workspace_service.properties.display_name }} and my parent workspace is {{ parent_workspace.properties.display_name }}"
    val = substitute_value(val_to_sub, primary_resource_dict, parent_ws_resource_dict, parent_ws_svc_resource_dict)
    assert val == "I am the primary resource ( a user resource - test_resource name), my workspace parent is ImTheParentWSSvc and my parent workspace is ImTheParentWS"


def test_simple_substitution(
    simple_pipeline_step, primary_resource, resource_to_update
):
    obj = substitute_properties(
        simple_pipeline_step, primary_resource, None, None, resource_to_update
    )

    assert obj["just_text"] == "Updated by 123"
    assert obj["just_text_2"] == "No substitution, just a fixed string here"
    assert obj["just_text_3"] == "Multiple substitutions -> 123 and template name"


def test_substitution_list_strings(primary_resource, resource_to_update):
    pipeline_step_with_list_strings = PipelineStep(
        properties=[
            PipelineStepProperty(
                name="obj_list_strings",
                type="string",
                value={
                    "name": "nrc_guacamole_svc_{{ resource.id }}",
                    "action": "Allow",
                    "rules": [
                        {
                            "name": "AllowAzureAD",
                            "description": "AAD access for authNZ",
                            "source_addresses": "",
                            "destination_addresses": ["AzureActiveDirectory"],
                            "destination_ports": ["*", "{{resource.id}}"],
                            "protocols": ["TCP"],
                        }
                    ],
                },
            )
        ]
    )
    obj = substitute_properties(
        pipeline_step_with_list_strings, primary_resource, None, None, resource_to_update,
    )

    assert obj["obj_list_strings"]["rules"][0]["destination_ports"] == ["*", "123"]


def test_substitution_props(pipeline_step, primary_resource, resource_to_update):
    obj = substitute_properties(pipeline_step, primary_resource, None, None, resource_to_update)

    assert obj["rule_collections"][0]["rules"][0]["target_fqdns"] == [
        "*pypi.org",
        "files.pythonhosted.org",
        "security.ubuntu.com",
    ]
    assert obj["rule_collections"][0]["rules"][0]["source_addresses"] == [
        "172.0.0.1",
        "192.168.0.1",
    ]
    assert (
        obj["rule_collections"][0]["rules"][0]["protocols"][1]["type"]
        == "MyCoolProtocol"
    )
    assert obj["rule_collections"][0]["rules"][0]["description"] == "Deployed by 123"


def test_substitution_array_append_remove(
    pipeline_step, primary_resource, resource_to_update
):

    # do the first substitution, and assert there's a single rule collection
    step = copy.deepcopy(pipeline_step)
    step.properties[0].arraySubstitutionAction = "append"
    step.properties[0].value["name"] = "object 1"
    obj = substitute_properties(step, primary_resource, None, None, resource_to_update)
    assert len(obj["rule_collections"]) == 1

    # in effect the RP will do this:
    resource_to_update.properties = obj

    # now append another substitution, and check we've got both rules
    step = copy.deepcopy(pipeline_step)
    step.properties[0].arraySubstitutionAction = "append"
    step.properties[0].value["name"] = "object 2"
    obj = substitute_properties(step, primary_resource, None, None, resource_to_update)
    assert len(obj["rule_collections"]) == 2

    # the RP makes the change again...
    resource_to_update.properties = obj

    # now append another substitution, and check we've got all 3 rules
    step = copy.deepcopy(pipeline_step)
    step.properties[0].arraySubstitutionAction = "append"
    step.properties[0].value["name"] = "object 3"
    obj = substitute_properties(step, primary_resource, None, None, resource_to_update)
    assert len(obj["rule_collections"]) == 3

    # the RP makes the change again...
    resource_to_update.properties = obj

    # now remove object 2...
    step = copy.deepcopy(pipeline_step)
    step.properties[0].arraySubstitutionAction = "remove"
    step.properties[0].value["name"] = "object 2"
    obj = substitute_properties(step, primary_resource, None, None, resource_to_update)
    assert len(obj["rule_collections"]) == 2
    assert obj["rule_collections"][0]["name"] == "object 1"
    assert obj["rule_collections"][1]["name"] == "object 3"

    # the RP makes the change again...
    resource_to_update.properties = obj

    # now remove object 1...
    step = copy.deepcopy(pipeline_step)
    step.properties[0].arraySubstitutionAction = "remove"
    step.properties[0].value["name"] = "object 1"
    obj = substitute_properties(step, primary_resource, None, None, resource_to_update)
    assert len(obj["rule_collections"]) == 1
    assert obj["rule_collections"][0]["name"] == "object 3"

    # the RP makes the change again...
    resource_to_update.properties = obj

    # now remove object 3...
    step = copy.deepcopy(pipeline_step)
    step.properties[0].arraySubstitutionAction = "remove"
    step.properties[0].value["name"] = "object 3"
    obj = substitute_properties(step, primary_resource, None, None, resource_to_update)
    assert len(obj["rule_collections"]) == 0

    # the RP makes the change again...
    resource_to_update.properties = obj

    # now remove another one, even though the array is empty...
    step = copy.deepcopy(pipeline_step)
    step.properties[0].arraySubstitutionAction = "remove"
    step.properties[0].value["name"] = "object 1"
    obj = substitute_properties(step, primary_resource, None, None, resource_to_update)
    assert len(obj["rule_collections"]) == 0


def test_substitution_array_append_replace(
    pipeline_step, primary_resource, resource_to_update
):

    # add object 1
    step = copy.deepcopy(pipeline_step)
    step.properties[0].arraySubstitutionAction = "append"
    step.properties[0].value["name"] = "Object 1"
    obj = substitute_properties(step, primary_resource, None, None, resource_to_update)
    assert len(obj["rule_collections"]) == 1
    assert obj["rule_collections"][0]["name"] == "Object 1"

    # the RP does this:
    resource_to_update.properties = obj

    # add object 2
    step = copy.deepcopy(pipeline_step)
    step.properties[0].arraySubstitutionAction = "append"
    step.properties[0].value["name"] = "Object 2"
    obj = substitute_properties(step, primary_resource, None, None, resource_to_update)
    assert len(obj["rule_collections"]) == 2
    assert obj["rule_collections"][1]["name"] == "Object 2"

    # the RP does this:
    resource_to_update.properties = obj

    # replace object 1
    step = copy.deepcopy(pipeline_step)
    step.properties[0].arraySubstitutionAction = "replace"
    step.properties[0].value["name"] = "Object 1"
    step.properties[0].value["action"] = "Deny Object 1"
    obj = substitute_properties(step, primary_resource, None, None, resource_to_update)
    assert len(obj["rule_collections"]) == 2
    assert obj["rule_collections"][0]["action"] == "Deny Object 1"

    # the RP does this:
    resource_to_update.properties = obj

    # replace the next one
    step = copy.deepcopy(pipeline_step)
    step.properties[0].arraySubstitutionAction = "replace"
    step.properties[0].value["name"] = "Object 2"
    step.properties[0].value["action"] = "Deny Object 2"
    obj = substitute_properties(step, primary_resource, None, None, resource_to_update)
    assert len(obj["rule_collections"]) == 2
    assert obj["rule_collections"][1]["action"] == "Deny Object 2"


def test_substitution_array_replace_not_found(
    pipeline_step, primary_resource, resource_to_update
):

    # try to replace an item not there - it should just append
    step = copy.deepcopy(pipeline_step)
    step.properties[0].arraySubstitutionAction = "replace"
    step.properties[0].value["name"] = "Object 1"
    obj = substitute_properties(step, primary_resource, None, None, resource_to_update)
    assert len(obj["rule_collections"]) == 1
    assert obj["rule_collections"][0]["name"] == "Object 1"
