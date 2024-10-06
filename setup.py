import os.path
import pathlib
import os
import pkg_resources
from setuptools import setup, find_packages

# with open("README.md", "r",encoding='utf-8-sig') as fh:
#     long_description = fh.read()



NAME = "paradoxism"
DIR = '.'

PACKAGES = find_packages(exclude= ["internal"])
print(PACKAGES)




with pathlib.Path('requirements.txt').open() as requirements_txt:
    install_requires = [
        str(requirement)
        for requirement
        in pkg_resources.parse_requirements(requirements_txt)
    ]

if  not  os.path.exists(os.path.join(os.path.expanduser('~'), ".paradoxism")):
    os.mkdir(os.path.join(os.path.expanduser('~'), ".paradoxism"))
if  not  os.path.exists(os.path.join(os.path.expanduser('~'), ".paradoxism/generate_images")):
    os.mkdir(os.path.join(os.path.expanduser('~'), ".paradoxism/generate_images"))
if  not  os.path.exists(os.path.join(os.path.expanduser('~'), ".paradoxism/download_pdfs")):
    os.mkdir(os.path.join(os.path.expanduser('~'), ".paradoxism/download_pdfs"))


setup(name=NAME,
      version='0.0.1',
      description='Prompt is all you need Liteon',
      # long_description=long_description,
      # long_description_content_type="text/markdown",
      long_description=open("README.md", encoding="utf-8").read(),
      long_description_content_type="text/markdown",
      author='Allan Yiin',
      author_email='allanyiin.ai@gmail.com',
      download_url='https://test.pypi.org/project/paradoxism',
      license='MIT',
      install_requires=install_requires,
      extras_require={
          'tests': ['pytest',
                    'pytest-pep8',
                    'pytest-xdist',
                    'pytest-cov',
                    'requests',
                    'markdown'],
      },
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Intended Audience :: Education',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: 3.11',
          'Topic :: Software Development :: Libraries',
          'Topic :: Software Development :: Libraries :: Python Modules'
      ],
      python_requires='>=3.7',
      keywords=['chatgpt', 'gpt4','llm','prompt'],
      packages= find_packages(exclude= [".idea"]),
      package_data={
          'paradoxism': ['oai.json','model_infos.json''examples/*.md'],
      },
      include_package_data=True,
      scripts=[],

      )

