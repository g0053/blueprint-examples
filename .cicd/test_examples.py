########
# Copyright (c) 2014-2019 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import pytest

from ecosystem_tests.dorkl import (
    blueprints_upload,
    basic_blueprint_test,
    cleanup_on_failure,
    prepare_test, vpn
)

from __init__ import (
    blueprint_id_filter,
    get_dirname_and_infra_name,
    blueprint_list,
    get_cloudify_version,
    VersionsException,
    PLUGINS_TO_UPLOAD,
    SECRETS_TO_CREATE)

prepare_test(plugins=PLUGINS_TO_UPLOAD,
             secrets=SECRETS_TO_CREATE,
             plugin_test=False,
             pip_packages=['boto', 'boto3', 'selinux'])

virtual_machine_list = [b for b in blueprint_list if 'virtual-machine'
                        in b and os.environ.get('IAAS', '') ==
                        os.path.basename(b).split('.yaml')[0]]
getting_started_list = [b for b in blueprint_list if 'getting-started' in b]
openshift_list = ['kubernetes/plugin-examples/openshift/blueprint.yaml']


@pytest.fixture(scope='function', params=blueprint_list)
def upload_blueprints_for_validation(request):
    blueprints_upload(request.param, blueprint_id_filter(request.param))


@pytest.fixture(scope='function', params=virtual_machine_list)
def basic_blueprint_test_with_getting_started_filter(request):
    _, infra_name = get_dirname_and_infra_name(request.param)
    blueprints_upload(request.param, 'infra-{0}'.format(infra_name))
    for blueprint_path in getting_started_list:
        blueprint_id = '{0}-{1}'.format(
            blueprint_id_filter(blueprint_path), infra_name)
        if 'vsphere' in infra_name:
            with vpn():
                try:
                    basic_blueprint_test(
                        blueprint_path,
                        blueprint_id,
                        inputs='infra_name={0} -i infra_exists=true'.format(
                            infra_name),
                        timeout=600)
                except:
                    cleanup_on_failure(blueprint_id)
                    raise
        else:
            try:
                basic_blueprint_test(
                    blueprint_path,
                    blueprint_id,
                    inputs='infra_name={0} -i infra_exists=true'.format(
                        infra_name),
                    timeout=600)
            except:
                cleanup_on_failure(blueprint_id)
                raise


@pytest.fixture(scope='function', params=openshift_list)
def openshift_test(request):
    try:
        basic_blueprint_test(
            request.param, blueprint_id_filter(request.param),
            inputs='namespace=blueprint-tests',
            timeout=3000)
    except:
        cleanup_on_failure(blueprint_id_filter(request.param))
        raise


def test_blueprint_validation(upload_blueprints_for_validation):
    """All blueprints must pass DSL validation."""
    assert upload_blueprints_for_validation is None


def test_versions():
    """All blueprints in this branch should be the same Cloudify version.
    """
    try:
        assert get_cloudify_version() is not None
    except VersionsException as e:
        pytest.fail(
            "Failed to verify that branch "
            "versions are the same: {0}.".format(str(e)))


def test_getting_started(basic_blueprint_test_with_getting_started_filter):
    assert basic_blueprint_test_with_getting_started_filter is None


def test_openshift(openshift_test):
    assert openshift_test is None

