from setuptools import setup, find_packages

setup(
    name="utterly",
    version="0.2.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click==8.1.8',
        'pyaudio==0.2.14',
        'pydub==0.25.1',
        'python-dotenv==1.0.1',
        'deepgram-sdk==3.10.1',
        'numpy==2.2.4',
        'pytz==2025.2',
        'soundfile==0.13.1',
        'sounddevice==0.5.1',
        'langchain==0.3.21',
        'langchain-openai==0.3.12',
        'langchain-prompty==0.1.1',
        'httpx==0.28.1',
        'verboselogs==1.7',
        'pyyaml==6.0.2',
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
