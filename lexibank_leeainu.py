from collections import defaultdict, OrderedDict
from six.moves import zip_longest as izip_longest

from clldutils.path import Path
from pylexibank.dataset import Dataset as BaseDataset
from clldutils.misc import slug
from cogsets import COGSET_MAP


class Dataset(BaseDataset):
    dir = Path(__file__).parent
    id = "leeainu"

    def cmd_download(self, **kw):
        self.raw.xls2csv("AinuHattoriChiri.xlsx")
        # TODO: Add sources.bib
        # self.raw.write('sources.bib', getEvoBibAsBibtex('Hattori1960', **kw))

    def cmd_install(self, **kw):
        concept_map = {c.gloss: c.id for c in self.concepticon.conceptsets.values()}
        meaning_map = {}
        language_map = {}
        wordlists = list(self.read_csv())
        cogsets = defaultdict(lambda: defaultdict(list))

        for wl in wordlists:
            for concept, (words, cogids) in wl.words.items():
                if len(cogids) == 1:
                    cogsets[concept][cogids[0]].append(words[0])

        with self.cldf as ds:
            for wl in wordlists:
                i = 0

                ds.add_language(ID=slug(wl.language), Name=wl.language, Glottocode="ainu1252")

                for concept, (words, cogids) in wl.words.items():
                    meaning_n = '{0}'.format(slug(concept))

                    if len(cogids) > 1:
                        if len(words) < len(cogids):
                            if len(words) == 1:
                                if ":" in words[0]:
                                    words = words[0].split(":")
                                if "," in words[0]:
                                    words = words[0].split(",")
                            assert len(words) >= len(cogids)
                        assert (wl.language, concept) in COGSET_MAP
                        if len(words) > len(cogids):
                            assert (wl.language, concept) in COGSET_MAP
                    if (wl.language, concept) in COGSET_MAP:
                        word_to_cogid = COGSET_MAP[(wl.language, concept)]
                    else:
                        word_to_cogid = dict(izip_longest(words, cogids))

                    if meaning_n not in meaning_map:
                        meaning_map[meaning_n] = '{0}_l{1}'.format(slug(concept), i)

                        ds.add_concept(ID=meaning_map[meaning_n], Name=concept,
                                       Concepticon_ID=concept_map.get(concept.upper()))
                    else:
                        ds.add_concept(ID=meaning_map[meaning_n], Name=concept,
                                       Concepticon_ID=concept_map.get(concept.upper()))

                    if concept.upper() not in concept_map:
                        self.unmapped.add_concept(ID=meaning_map[meaning_n], Name=concept)

                    i += 1

                    for i, word in enumerate(words):
                        if word.startswith("(") and word.endswith(")"):
                            word = word[1:-1].strip()
                        for row in ds.add_lexemes(
                            Language_ID=slug(wl.language),
                            Parameter_ID=meaning_map[meaning_n],
                            Value=word,
                            Source=["Hattori1960"],
                        ):
                            if word_to_cogid.get(word):
                                ds.add_cognate(
                                    lexeme=row,
                                    Cognateset_ID="%s-%s" % (slug(concept), word_to_cogid[word]),
                                    # TODO: Cognate_source="Hattori1960",
                                )

    def read_csv(self, fname="AinuHattoriChiri.Sheet1.csv", **kw):
        header = None
        for i, row in enumerate(self.raw.read_csv(fname)):
            row = [c.strip() for c in row]
            if i == 1:
                header = row[2:]
            if i > 2:
                wl = Wordlist(row[1])
                words, concept = None, None
                for j in range(len(header)):
                    if header[j]:
                        # a column containing words
                        if words:
                            assert concept
                            wl.words[concept] = (words, [])
                            words, concept = None, None
                        words = row[j + 2].split(";")
                        concept = header[j]
                    else:
                        # a column containing cognate set IDs
                        assert concept
                        words = [w for w in words if w and w != "#"]
                        if words:
                            wl.words[concept] = (
                                words,
                                [int(float(k)) for k in row[j + 2].split("&") if k != "#"],
                            )
                        words, concept = None, None
                yield wl


class Wordlist:
    def __init__(self, language):
        self.language = language
        self.words = OrderedDict()
