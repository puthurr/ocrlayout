# Ocrlayout Library

Provides the ability to get more meaninful output from common OCR responses by manipulating Bounding Boxes.

Current OCR engines responses are focus on text recall. Ocrlayout tries to go a step further by re-ordering the lines of text so it'd approach a human-reading behavior. 

## Problem Statement
When processing images containing lots of textual information, it becomes relevant to assemble the generated text into meaninful blocks of text. 
While OCR engines responses are fine for recall, they aren't necessary generating meaningfull output text for further Text processing. 

## More meaningfull output for what? 
- **Text Analytics** you may leverage any Text Analytics such as Key Phrases, Entities Extraction with more confidence of its outcome
- **Accessibility** : Any infographic becomes alive, overcoming the alt text feature.
- **Read Aloud feature** : it becomes easier to build solutions to read aloud an image, increasing verbal narrative of visual information. 
- **Machine Translation** : get more accurate MT output as you can retain more context. 
- **Sentences/Paragraph Classification**: from scanned-base images i.e. contracts, having a more meaninful textual output allows you to classify it at a granular level in terms of risk, personal clause or conditions. 

## OCR Engines Support
We support Azure, Google & AWS text extraction OCR API.

>Our goal here is not to conduct a comparison between all 3 majors providers but to provide a consistent way to output OCR text for further processing regardless of the underlying OCR Engine. 

* [Azure Computer Vision - Read API](https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/concept-recognizing-text#read-api)
* [Azure Computer Vision - OCR API](https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/concept-recognizing-text#ocr-api)
* [Google Vision API - Detect Text](https://cloud.google.com/vision/docs/ocr#vision_text_detection-python)
* [AWS Textextract - Detecting Text](https://docs.aws.amazon.com/textract/latest/dg/how-it-works-detecting.html)

## Examples
Check out our **Examples** section to get a better feeling on how Bounding Box Helper could support better your OCR-related projects. 

### DISCLAIMER
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.