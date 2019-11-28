import pathlib
import itertools
import collections

from pylexibank import Dataset as BaseDataset
from clldutils.misc import slug
from cogsets import COGSET_MAP


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "leeainu"

    def cmd_download(self, args):
        self.raw_dir.xls2csv("AinuHattoriChiri.xlsx")

    def cmd_makecldf(self, args):
        meaning_map = {}
        wordlists = list(self.read_csv())
        cogsets = collections.defaultdict(lambda: collections.defaultdict(list))

        for wl in wordlists:
            for concept, (words, cogids) in wl.words.items():
                if len(cogids) == 1:
                    cogsets[concept][cogids[0]].append(words[0])

        args.writer.add_sources(*self.raw_dir.read_bib())
        lmap = args.writer.add_languages(lookup_factory='Name')

        for concept in self.concepts:
            args.writer.add_concept(
                ID=slug(concept["ENGLISH"]),
                Name=concept["ENGLISH"],
                Concepticon_ID=concept["CONCEPTICON_ID"],
            )
            meaning_map[slug(concept["ENGLISH"])] = slug(concept["ENGLISH"])

        args.writer.add_concept(ID=slug("YEAR"), Name="year", Concepticon_ID="1226")
        meaning_map["year"] = "year"

        for wl in wordlists:
            for concept, (words, cogids) in wl.words.items():
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
                    word_to_cogid = dict(itertools.zip_longest(words, cogids))

                for i, word in enumerate(words):
                    if word.startswith("(") and word.endswith(")"):
                        word = word[1:-1].strip()
                    for row in args.writer.add_lexemes(
                        Language_ID=lmap[wl.language],
                        Parameter_ID=meaning_map[slug(concept)],
                        Value=word,
                        Source=["Hattori1960"],
                    ):
                        if word_to_cogid.get(word):
                            args.writer.add_cognate(
                                lexeme=row,
                                Cognateset_ID="%s-%s" % (slug(concept), word_to_cogid[word]),
                                Source="Hattori1960",
                            )

    def read_csv(self, fname="AinuHattoriChiri.Sheet1.csv"):
        header = None
        for i, row in enumerate(self.raw_dir.read_csv(fname)):
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
        self.words = collections.OrderedDict()
