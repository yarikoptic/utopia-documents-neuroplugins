#emacs: -*- mode: python-mode; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*- 
#ex: set sts=4 ts=4 sw=4 noet:
"""

 COPYRIGHT: Yaroslav Halchenko 2014

 LICENSE: MIT

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in
  all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
  THE SOFTWARE.
"""

__author__ = 'Yaroslav Halchenko'
__copyright__ = 'Copyright (c) 2014 Yaroslav Halchenko'
__license__ = 'MIT'

import utopia.document
import spineapi
import urllib

class NeuroSynthAnnotator(utopia.document.Annotator):
    """Annotates text with urls pointing to NeuroSynth"""

    @utopia.document.buffer # Wrap/buffer the function
    def on_activate_event(self, document):

        regex = r'(functional abnormalities)'
        # Scan the document for some regular expression
        matches = document.search(regex,
            spineapi.RegExp + spineapi.WholeWordsOnly)

        to_add = {} # Dictionary of annotations to add

        for match in matches:
            # Sanitise matches found in document for dict keys
            match_text = match.text().lower().strip()
            match_text_quoted = urllib.quote(match_text)

            # Has same text already been annotated?
            annotation = to_add.get(match_text, None)

            if annotation is None:
                # If no, create new annotation
                annotation = spineapi.Annotation()
                annotation['concept'] = 'NeuroSynthAnnotation'
                annotation['property:name'] = match_text
                annotation['property:description'] = 'Link to NeuroSynth'
                annotation['property:webpageUrl'] = 'http://beta.neurosynth.org/features/{0}/'.format(match_text_quoted)
                annotation['session:overlay'] = 'hyperlink'
                annotation['session:color'] = '#00AA00' # Green
                to_add[match_text] = annotation

            if annotation is not None:
                # Add the match to the annotation, in any case
                annotation.addExtent(match)

            # Finally, add the annotations to the document
            document.addAnnotations(to_add.values())
