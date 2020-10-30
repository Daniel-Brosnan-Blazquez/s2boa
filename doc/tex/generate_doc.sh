#################################################################
#
# Generate  documentation for the s2boa component
#
# Written by DEIMOS Space S.L. (dibb)
#
# module s2boa
#################################################################
USAGE="Usage: `basename $0` -f pdf_file [-k]\n
Optional parameters:\n
-k: if set it indicates the script to keep the build directory
"
if [ -z "$EBOA_RESOURCES_PATH" ];
then
    echo -e "ERROR: The environment variable EBOA_RESOURCES_PATH has to be defined"
    echo -e $USAGE
    exit -1
fi

PDF_FILE=""
KEEP_BUILD="NO"

while getopts kf:d: option
do
    case "${option}"
        in
            f) PDF_FILE=${OPTARG};;
            d) WORKING_DIRECTORY=${OPTARG};;
            k) KEEP_BUILD="YES";;
            ?) echo -e $USAGE
            exit -1
    esac
done

# Check that option -f has been specified
if [ "$PDF_FILE" == "" ];
then
    echo -e "ERROR: The option -f has to be provided"
    echo -e $USAGE
    exit -1
fi

# Check that option -d has been specified
if [ "$WORKING_DIRECTORY" == "" ];
then
    echo -e "ERROR: The option -d has to be provided"
    echo -e $USAGE
    exit -1
fi

# Check the working directory exists
if [ ! -d $WORKING_DIRECTORY ];
then
    echo -e "ERROR: The working directory specified does not exist: " $WORKING_DIRECTORY
    echo -e $USAGE
    exit -1
fi

# Check that working directory contains a doc.tex
if [ ! -f $WORKING_DIRECTORY/doc.tex ];
then
    echo -e "ERROR: The working directory does not contain a doc.tex file: " $WORKING_DIRECTORY/doc.tex
    echo -e $USAGE
    exit -1
fi

# Create the build directory
if [ -d $WORKING_DIRECTORY/build ];
then
    rm -rf $WORKING_DIRECTORY/build
fi
mkdir $WORKING_DIRECTORY/build

# Automatically Extract the documentation from the python code
## S2BOA
# Generate the tex file
sphinx-build -b latex $WORKING_DIRECTORY/../../src/docs/s2boa/ $WORKING_DIRECTORY/build
# Add chapter part
echo "\chapter{Ingestion modules code documentation}" > $WORKING_DIRECTORY/s2boa_code_documentation.tex
# Extract the chapter describing the code
sed -n '/\\section{Subpackages}/,/\\section{Module contents}/p' $WORKING_DIRECTORY/build/S2BOA_module.tex |head -n -1 >> $WORKING_DIRECTORY/s2boa_code_documentation.tex

## S2VBOA
# Generate the tex file
sphinx-build -b latex $WORKING_DIRECTORY/../../src/docs/s2vboa/ $WORKING_DIRECTORY/build
# Add chapter part
echo "\chapter{View modules code documentation}" > $WORKING_DIRECTORY/s2vboa_code_documentation.tex
# Extract the chapter describing the code
sed -n '/\\section{Subpackages}/,/\\section{Module contents}/p' $WORKING_DIRECTORY/build/S2VBOA_module.tex |head -n -1 >> $WORKING_DIRECTORY/s2vboa_code_documentation.tex

# Execute the first translation of the tex files into a PDF file
TEXINPUTS=".:"$WORKING_DIRECTORY":"$WORKING_DIRECTORY/../fig":" pdflatex -output-directory $WORKING_DIRECTORY/build -halt-on-error -interaction=nonstopmode $WORKING_DIRECTORY/doc.tex &> /dev/null

# Generate glossaries
makeglossaries -d $WORKING_DIRECTORY -s build/doc.ist build/doc &> /dev/null

# Execute last translation to generate the PDF with the glossaries
TEXINPUTS=".:"$WORKING_DIRECTORY":"$WORKING_DIRECTORY/../fig":" pdflatex -output-directory $WORKING_DIRECTORY/build -halt-on-error -interaction=nonstopmode $WORKING_DIRECTORY/doc.tex |grep -i "warning\|error"

# Move generated pdf to its 
if [ -f $WORKING_DIRECTORY/build/doc.pdf ];
then
    mv $WORKING_DIRECTORY/build/doc.pdf $WORKING_DIRECTORY/$PDF_FILE
else
    echo -e "ERROR: There was an error on the generation of the PDF.\nIs pdflatex installed?"
fi

if [ "$KEEP_BUILD" != "YES" ];
then
    rm -rf $WORKING_DIRECTORY/build
fi
