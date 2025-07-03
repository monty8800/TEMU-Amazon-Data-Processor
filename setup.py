import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="temu-amazon-processor",
    version="1.2.2",
    author="monty8800",
    author_email="monty8800@example.com",
    description="TEMU & Amazon数据处理系统",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/monty8800/TEMU-Amazon-Data-Processor",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas>=1.5.0",
        "openpyxl>=3.0.10",
        "chardet>=4.0.0",
        "colorama>=0.4.4",
    ],
    package_data={
        "": ["*.json"],
    },
    entry_points={
        "console_scripts": [
            "temu-processor=temu_amazon_processor.main:main",
        ],
    },
)
