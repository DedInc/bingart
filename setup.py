from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='bingart',
    version='1.0.2',
    author='Maehdakvan',
    author_email='visitanimation@google.com',
    description='bingart is an unofficial API wrapper for Bing Image Creator (based on DALL-E 3).',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/DedInc/bingart',
    project_urls={
        'Bug Tracker': 'https://github.com/DedInc/bingart/issues',
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    packages=find_packages(),
    include_package_data = True,
    install_requires = ['requests'],
    python_requires='>=3.6'
)