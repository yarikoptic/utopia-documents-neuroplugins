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

import re
import utopia.document
import spineapi
import urllib, urllib2, json

_debug_file = open('/tmp/debug.log', 'a')

def _debug(s):
    _debug_file.write("%s\n" % s)
    _debug_file.flush()

_debug("starting")


class _GenericAnnotator(utopia.document.Annotator):
    """Annotates text with urls pointing to a website.

    Derived classes should specialize with the list of terms, and
    generating URL per given term
    """

    _name = None

    def get_terms(self):
        raise NotImplementedError

    def get_url(self, term):
        raise NotImplementedError


    def get_terms_regex(self):
        terms = self.get_terms()
        _debug("Got %d terms" % len(terms))
        r = r'(%s)' % '|'.join(terms)
        _debug("IS IT THERE: %s" % ("functional abnormalities" in r))
        _debug(r)
        return r # re.compile("functional abnormalities")
        #return re.compile("(functional abnormalities|structural abnormalities|temporoparietal junction|ventrolateral prefrontal)")

    @utopia.document.buffer # Wrap/buffer the function
    #def on_ready_event(self, document):
    def on_activate_event(self, document):
        _debug('activate base')
        # Scan the document for some regular expression
        matches = document.search(
            self.get_terms_regex(),
            spineapi.RegExp
            + spineapi.WholeWordsOnly
            + spineapi.IgnoreCase
            )

        to_add = {} # Dictionary of annotations to add

        try:
          for match in matches:
            _debug("Match %s" % str(match))
            # Sanitise matches found in document for dict keys
            match_text = match.text().lower().strip()

            # Has same text already been annotated?
            annotation = to_add.get(match_text, None)

            if annotation is None:
                # If no, create new annotation
                annotation = spineapi.Annotation()
                annotation['concept'] = 'Annotation %s' % self._name
                annotation['property:name'] = match_text
                annotation['property:description'] = 'Link to %s' % self._name
                annotation['property:webpageUrl'] = self.get_url(match_text)
                annotation['session:overlay'] = 'hyperlink'
                annotation['session:color'] = '#00AA00' # Green
                to_add[match_text] = annotation

            if annotation is not None:
                # Add the match to the annotation, in any case
                _debug("Added %s" % str(annotation))
                annotation.addExtent(match)
        except Exception, e:
            _debug("ERROR: %s" % str(e))

        # Finally, add the annotations to the document
        document.addAnnotations(to_add.values())
        _debug('finished activate base')


from static_data import NEUROSYNTH_TERMS


class NeuroSynthAnnotator(_GenericAnnotator,
                          utopia.document.Visualiser):
    """URLs pointing to NeuroSynth"""

    _name = "NeuroSynth"
    # beta.neurosynth API is non-functioning atm, so here are the features
    _features = NEUROSYNTH_TERMS

    def get_terms(self):
        #return self._features
        return [x for x in self._features if len(x)>5]

    def get_url(self, term):
        term_quoted = urllib.quote(term)
        return 'http://beta.neurosynth.org/features/{0}/'.format(term_quoted)

    def visualisable(self, annotation):
        r = annotation.get('concept', '') == 'Annotation %s' % self._name
        _debug("visualizable: %s" % r)
        return r

    def visualise(self, annotation):
        html = '<p>{0}</p>'.format("bleh blah")
        _debug("Visualizing: %s" % html)
        return html



class _NeuroElectroAnnotator(_GenericAnnotator):
    """URLs pointing to NeuroElectro"""

    _name = "NeuroElectro"

    def get_terms(self):
        u = urllib2.urlopen('http://neuroelectro.org/api/1/n/')
        neurons = json.load(u)
        self._neurons_mapping = dict([(n['name'].lower(), n['id']) for n in neurons['objects']])
        return self._neurons_mapping.keys()

    def get_url(self, term):
        return 'http://www.neuroelectro.org/neuron/%d/' % (self._neurons_mapping[term.lower()])

from static_data import NEUROVAULT_COLLECTIONS_ID2
import common.utils


class NeuroVaultAnnotator(utopia.document.Annotator):
    '''Connect to NeuroVault service.'''

    API_URL = "http://neurovault.org/api"
    IMAGES_URL = "http://neurovault.org/images/%s"

    def _get_collection_by_doi(self, doi):
        if doi is None:
            return None
        print "DOI: %r" % doi
        if doi.lower() != u"10.1016/j.neuroimage.2012.12.012":
            raise NotImplementedError("https://github.com/NeuroVault/NeuroVault/issues/38")
        return json.loads(NEUROVAULT_COLLECTIONS_ID2)

    def _get_collection_images(self, col):
        if col is None:
            return None
        print "COL: %r" % col
        if col['id'] == 2:
            return ("2",)
        else:
            raise NotImplementedError("https://github.com/NeuroVault/NeuroVault/issues/39")

    def _get_image_metainfo(self, image):
        url = "{url}/images/{image}/?format=json".format(url=self.API_URL, image=image)
        print "URL: %r" % url
        u = urllib2.urlopen(url)
        return json.load(u)

    def on_ready_event(self, document):
        doi = common.utils.metadata(document, 'doi')
        if doi is None:
            return None
        collection = self._get_collection_by_doi(doi)
        if not collection:
            return None
        image_ids = self._get_collection_images(collection)
        htmls = []
        for image_id in image_ids:
            info = self._get_image_metainfo(image_id)
            if not info:
                continue
            info['url'] = self.IMAGES_URL % image_id
            info['image_id'] = image_id
            html = u'''
             <div id="{image_id}" class="box">
              <p>
               <span class="name">{name}</span> /
               <span class="map_type">{map_type}</span> /
               <span class="title"><a href="{url}" title="View in NeuroVault">{description}</a></span>
              </p>
             </div>'''.format(**info)
            htmls.append(html)

        if len(htmls) > 0:
            annotation = spineapi.Annotation()
            annotation['concept'] = 'NeuroVaultReference'
            annotation['property:html'] = ''.join(htmls)
            annotation['property:name'] = 'NeuroVault'
            annotation['property:description'] = 'Publicly available supplementary data'
            annotation['property:sourceDatabase'] = 'neurovault'
            annotation['property:sourceDescription'] = '<p><a href="http://neurovault.org/">Neuro<strong>Vault</strong></a> allows neuroimaging researchers to publish their full resultant statistical maps to  supplement their publications.</p>'
            document.addAnnotation(annotation)


class NeuroVaultVisualiser(utopia.document.Visualiser):
    '''Visualise NeuroVault references.'''

    def visualisable(self, annotation):
        return annotation.get('concept') == 'NeuroVaultReference'

    def visualise(self, annotation):
        return ('<style>#neurovault .authors { font-style: italic }</style>',
                '<div id="neurovault">' + annotation['property:html'] + '</div>')
