from setuptools import setup, find_packages
import os

def get_dependencies(req_path, header):
    with open(req_path, 'r') as requirements_file:
        deps = []
        start_reading = False
        for line in requirements_file:
            if not start_reading:
                if line.startswith(f'# {header}'):
                    start_reading = True
            else:
                if line.startswith('#'):
                    return deps
                if len(line) > 0 and line[0] != '#':
                    deps.append(line.strip())

        return deps


REQUIREMENTS_FILENAME = 'requirements.txt'
INSTALL_DEPS_HEADER = 'INSTALL_DEPENDENCIES'
TEST_DEPS_HEADER = 'TEST_DEPENDENCIES'

requirements_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), REQUIREMENTS_FILENAME)
test_deps = get_dependencies(requirements_path, TEST_DEPS_HEADER)
install_deps = get_dependencies(requirements_path, INSTALL_DEPS_HEADER)

setup(
    name='dart_lambdas',
    version='3.0.0',
    description='Send files from S3 ingest bucket to Ladle, and then move to S3 processed bucket',
    author='John Hungerford',
    author_email='john.hungerford@twosixlabs.com',
    packages=find_packages(),
    install_requires=install_deps,
    setup_requires=['pytest-runner'],
    tests_require=test_deps,
    extras_require={'test': test_deps},
    include_package_data=True,
)
