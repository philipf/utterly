from setuptools import setup, find_packages

setup(
    name="utterly",
    version="0.2.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        'pyaudio',
        'pydub',
        'python-dotenv',
        'deepgram-sdk',
        'numpy',
        'pytz',
        'soundfile',
        'sounddevice',
        'langchain',
        'langchain-openai',
        'langchain-prompty',
        'httpx',
        'verboselogs',
        'pyyaml',
    ],
    entry_points={
        'console_scripts': [
            'utterly=utterly.cli:main',
        ],
    },
    author="Philip Fourie",
    description="A CLI tool for managing meeting recordings, transcriptions, and summaries",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/philipf/utterly",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12",
)