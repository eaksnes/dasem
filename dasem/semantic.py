"""Semantic.

Usage:
  dasem.semantic relatedness [options] <phrases>...
  dasem.semantic related [options] <phrase>
  dasem.semantic sort-by-outlierness [options] <phrases>...

Options:
  -h --help
  --display
  --max-n-pages=<int>

"""

from __future__ import division, print_function

import numpy as np

from six import print_, u

import sys

from sklearn.feature_extraction.text import TfidfVectorizer

from tqdm import tqdm

from .wikipedia import XmlDumpFile


class Semantic(object):
    """Semantic.

    Examples
    --------
    >>> semantic = Semantic(30000)  # and wait
    >>> semantic.relatedness(['hund', 'kat', 'hus', 'vindue']).round(3)
    array([[ 1.   ,  0.014,  0.001,  0.   ],
           [ 0.014,  1.   ,  0.002,  0.   ],
           [ 0.001,  0.002,  1.   ,  0.027],
           [ 0.   ,  0.   ,  0.027,  1.   ]])

    """

    def __init__(self, max_n_pages=None, display=False):
        self.setup_wikipedia_semantics(
            max_n_pages=max_n_pages, display=display)

    def setup_wikipedia_semantics(self, max_n_pages=None, display=False):
        self._dump_file = XmlDumpFile()

        self._wikipedia_titles = [
            page['title'] for page in self._dump_file.iter_article_pages(
                max_n_pages=max_n_pages,
                display=display)]

        texts = (page['text']
                 for page in self._dump_file.iter_article_pages(
                         max_n_pages=max_n_pages,
                         display=display))

        if display:
            tqdm.write('TFIDF vectorizing')
        self._wikipedia_transformer = TfidfVectorizer()
        self._wikipedia_Y = self._wikipedia_transformer.fit_transform(texts)

    def relatedness(self, phrases):
        """Return semantic relatedness between two phrases.

        Parameters
        ----------
        phrases : list of str
            List of phrases as strings.

        Returns
        -------
        relatedness : np.array
            Array with value between 0 and 1 for semantic relatedness.

        """
        Y = self._wikipedia_transformer.transform(phrases)
        D = np.asarray((self._wikipedia_Y * Y.T).todense())
        D = np.einsum('ij,j->ij', D,
                      1 / np.sqrt(np.multiply(D, D).sum(axis=0)))
        return D.T.dot(D)

    def related(self, phrase, n=10):
        """Return related articles.

        Parameters
        ----------
        phrase : str
            Phrase
        n : int
            Number of articles to return.

        Returns
        -------
        titles : list of str
            List of articles as strings.

        """
        if n is None:
            n = 10
        y = self._wikipedia_transformer.transform([phrase])
        D = np.array((self._wikipedia_Y * y.T).todense())
        indices = np.argsort(-D, axis=0)
        titles = [self._wikipedia_titles[index] for index in indices[:n, 0]]
        return titles

    def sort_by_outlierness(self, phrases):
        """Return phrases based on outlierness.

        Parameters
        ----------
        phrases : list of str
            List of phrases.

        Returns
        -------
        sorted_phrases : list of str
            List of sorted phrases.

        Examples
        --------
        >>> semantic = dasem.semantic.Semantic(20000)
        >>> semantic.sort_by_outlierness(['hund', 'fogh', 'nyrup', 'helle'])
        ['hund', 'nyrup', 'fogh', 'rasmussen']

        """
        R = self.relatedness(phrases)
        indices = np.argsort(R.sum(axis=0) - 1)
        return [phrases[idx] for idx in indices]


def main():
    reload(sys)
    sys.setdefaultencoding(sys.stdout.encoding)

    from docopt import docopt

    arguments = docopt(__doc__)
    display = arguments['--display']
    if arguments['--max-n-pages']:
        max_n_pages = int(arguments['--max-n-pages'])
    else:
        max_n_pages = None
    # TODO: encoding
    phrase = arguments['<phrase>']
    phrases = arguments['<phrases>']

    if arguments['relatedness']:
        semantic = Semantic(max_n_pages=max_n_pages, display=display)
        relatedness = semantic.relatedness(phrases)
        print(relatedness)

    elif arguments['related']:
        semantic = Semantic(max_n_pages=max_n_pages, display=display)
        titles = semantic.related(phrase)
        separator = u('\n')
        print(separator.join(titles))

    elif arguments['sort-by-outlierness']:
        semantic = Semantic(max_n_pages=max_n_pages, display=display)
        sorted_phrases = semantic.sort_by_outlierness(phrases)
        separator = u('\n')
        print_(separator.join(sorted_phrases))


if __name__ == '__main__':
    main()