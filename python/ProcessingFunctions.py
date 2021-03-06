"""
Create help functions to call when running scripts
"""
from python.ConfigUser import path_project
import xlsxwriter
from textdistance import jaro
from spacy.lang.de import German
from spacy.tokenizer import Tokenizer
import spacy
import re
from germalemma import GermaLemma


def MakeListInLists(string):
    """
    make lists nested in list, this is used for reading in exported, preprocessed articles and to prepare them
    in the appropriate format we need for running lda
    """
    listinlist = []
    for n in string:
        help = []
        m = n.replace('[', '').replace(']', '').replace('\'', '')
        m = m.split(', ')
        for o in m:
            help.append(o)
        listinlist.append(help[0:(len(help[0]) - 1)])
    return listinlist


# function to flatten lists
FlattenList = lambda l: [element for sublist in l for element in sublist]


def ListToFreqDict(wordlist):
    """
    reads in a list, counts words, puts them into a dictionary ans sorts them reversed
    """
    wordfreq = [wordlist.count(p) for p in wordlist]
    help = dict(list(zip(wordlist, wordfreq)))
    # sort ascending
    # help = sorted(help.items(), key=lambda kv: kv[1])
    # sort descending
    help = sorted(help.items(), reverse=True, key=lambda kv: kv[1])
    return help


def ExportFreqDict(wordlist, path=path_project + 'data/', filename='frequency_wordlist.xlsx'):
    """
    exports the produced frequency-wordlist from ListToFreqDict to an excel file
    input: so list with tuples with the form [(,),(,),...]
    """
    workbook = xlsxwriter.Workbook(path + filename)
    worksheet = workbook.add_worksheet()
    row, col = 1, 0
    worksheet.write(0, 0, 'word')
    worksheet.write(0, 1, 'frequency')
    for el in wordlist:
        worksheet.write(row, col, el[0])
        worksheet.write(row, col + 1, el[1])
        row += 1
    workbook.close()


def GetUniqueStrings(list, threshold=.9, verbose=False):
    """
    input: list with strings
    param: threshold, verbose
    return: 2 lists, one with unique strings, one with unique indizes
    """
    list.sort(key=len)
    unique_flag = True
    unique_strings, unique_index = [], []
    for i, l1 in enumerate(list):
        unique_flag = True
        if verbose: print(i, l1)
        for j in range(i + 1, len(list)):
            l2 = list[j]
            similarity_index = jaro(l1, l2)
            if similarity_index >= threshold:
                # if similiar, don't append to unique lists
                if verbose: print('similar strings:\n[{}] {}\n[{}] {}\n'.format(i, l1, j, l2))
                unique_flag = False
                continue
            else:
                unique_flag = True
        if unique_flag:
            unique_index.append(i)
            unique_strings.append(l1)
    return unique_index, unique_strings


def RemoveBlankElements(list):
    return [x.strip() for x in list if x.strip()]


def DateRemover(string):
    """
    remove dates of the format: 25. februar, OR 10, mai OR 1juni OR 8./9. juni OR 8., 9. juni OR 8.-9. juni OR 8. 9. juni
    run first, before NumberComplexRemover()
    """
    for month in ['januar', 'februar', 'märz', 'april', 'mai', 'juni', 'juli', 'august', 'september', 'oktober',
                  'november', 'dezember']:
        string = re.sub('\d+([.]\s+|\s+|)({})'.format(month), ' {} '.format(month), string)
    string = re.sub('\d+([.]|[.]\s+|\s+|)jahrhundert', 'jahrhundert', string)
    return string


def NumberComplexRemover(string):
    """
    removes numbers in complex format, but not if a . is followed as it introduces the end of a sentence.
    run after DateRemover()
    Examples: 15.10 Uhr OR 3,5 bis 4 stunden. OR 100 000 euro. OR 20?000 förderanträge OR um 2025/2030 OR
    OR abc 18.000. a OR abc. 18.000. a OR abc 18. a  OR abc 7.8.14. a  OR abc 7. 14. 18. a OR abc 1970er. a
    OR abc 20?()/&!%000. a  OR abc 2,9-3,5. a OR abc . 18. a OR abc . 7.8.14. a OR abc . 7. 14. 18. a OR abc 1790er
    OR abc . 20?()/&!%000 a  OR abc . 2,9-3,5 a OR abc 45, 59 a OR abc . 14 z OR abc  1. e OR abc  v. 2 a
    """
    string = re.sub('(?<!\w)(\d+)([\W\s]+|)|([\W\s]+)\d+', ' ', string)  # TODO: check later
    # Alternative: ((\d+)(.|\s{1,3}|)\d+)(.|\s)(?! er)
    return string


nlp = German()
sbd = nlp.create_pipe('sentencizer')
nlp.add_pipe(sbd)


def Sentencizer(string):
    """
    requires from importing language from spacy and loading of sentence boundary detection:
    from spacy.lang.de import German
    nlp = German()
    sbd = nlp.create_pipe('sentencizer')
    nlp.add_pipe(sbd)
    """
    doc = nlp(string)
    sents_list = []
    for sent in doc.sents:
        sents_list.append(sent.text)
    return sents_list


def SentenceWordRemover(listOfSents, dropWords):
    """
    drop words from listOfSents which are specified in dropWords
    """
    cleanedlistOfSents = []
    for sent in listOfSents:
        temp_sent = sent
        for word in dropWords:
            temp_sent = re.sub('(?<![-/&]|\w){}(?![-/&]|\w)'.format(word), '', temp_sent)
        cleanedlistOfSents.append(temp_sent)
    return cleanedlistOfSents


def SentenceLinkRemover(listOfSents):
    """
    removes any kind of link
    """
    cleanedlistOfSents = []
    for sent in listOfSents:
        temp_sent = re.sub(
            r'''(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))''',
            " ", sent)
        cleanedlistOfSents.append(temp_sent)
    return cleanedlistOfSents


def SentenceMailRemover(listOfSents):
    """
    removes mail addresses
    """
    cleanedlistOfSents = []
    for sent in listOfSents:
        temp_sent = re.sub(r'\S+@\S+', ' ', sent)
        cleanedlistOfSents.append(temp_sent)
    return cleanedlistOfSents


def SentenceCleaner(listOfSents):
    """
    cleans trash hyphens, special characters and punctuations;
    apply loop fct to each list in pandas cell
    """
    p = re.compile(r"(\b[-'/.&]\b)|[\W_]")  # TODO: check later - getestet DW, passt!
    return [p.sub(lambda m: (m.group(1) if m.group(1) else " "), x) for x in listOfSents]


nlp2 = spacy.load('de_core_news_md', disable=['ner', 'parser'])

def SentencePOStagger(listOfSents, POStag='NN'):
    """
    POS tag words in sentences
    """
    POStaggedlist = []
    for sent in listOfSents:
        list, sent_tokens = nlp2(sent), []
        for token in list:
            if token.tag_.startswith(POStag): sent_tokens.append(token)
        POStaggedlist.append(sent_tokens)
    return POStaggedlist


# Load Lemmatization
lemmatizer = GermaLemma()


def SentenceLemmatizer(listOfSents):
    """
    Lemmatizer of POS tagged words in sentences. Run this fct after SentencePOStagger()
    """
    lemmalist = []
    for sent in listOfSents:
        lemmalist.append([])
        for token in sent:
            token_lemma = lemmatizer.find_lemma(token.text, token.tag_)
            token_lemma = token_lemma.lower()
            lemmalist[-1].append(token_lemma)
    return lemmalist


def SentenceTokenizer(listOfSents):
    """
    load SetupTokenizer() first
    """
    # Set up tokenizer
    tokenizer = Tokenizer(nlp.vocab)
    tokenizer = nlp.Defaults.create_tokenizer(nlp)

    tokenizedlist = []
    for sent in listOfSents:
        tokenizedlist.append(tokenizer(sent))
    return tokenizedlist


def SentenceCleanTokens(listOfSents, minwordinsent, minwordlength):
    """
    drop sentences (=sent) which are too short and have only 2 or less words
    """
    cleanedlistOfSents = []
    for sent in listOfSents:
        filteredSent = []
        # if sentence (list) is empty, skip it. More precise: Drop if list-length<3 and word-length<3
        if (len(sent) >= minwordinsent):
            for word in sent:
                # filter out stop words and blanks elements
                if len(word) >= minwordlength:
                    filteredSent.append(word)
            # append filtered sentence list to cleaned list of sentences only if it still contained 3 words or more
            if (len(filteredSent) >= minwordinsent):
                cleanedlistOfSents.append(filteredSent)
    return cleanedlistOfSents


def NormalizeWords(string):
    """
    Normalize Words (Preserve words by replacing to synonyms and write full words instead abbrev.)
    """

    # Normalize e-mobility related words
    string = string.replace('co2', 'kohlenstoffdioxid').replace('co²', 'kohlenstoffdioxid').replace('co 2',
                                                                                                    'kohlenstoffdioxid')
    string = string.replace('km/h', 'kilometerprostunde').replace('km-h', 'kilometerprostunde').replace('km /h',
                                                                                                        'kilometerprostunde')
    string = string.replace('g/km', 'grammprokilometer').replace('g-km', 'grammprokilometer').replace('g /km',
                                                                                                      'grammprokilometer')
    string = string.replace('g/cm³', 'grammprokubikmeter').replace('cm³', 'kubikmeter')
    string = string.replace('/km', 'prokilometer').replace('km', 'kilometer')
    string = string.replace('m-s', 'meterprosekunde').replace('m/s', 'meterprosekunde')
    string = string.replace('mio.', 'millionen').replace('mrd.', 'milliarden').replace('mill.', 'millionen')
    string = string.replace('kwh', 'kilowattstunde').replace('mwh', 'megawattstunde').replace('kw/h', 'kilowattstunde')
    string = string.replace('kw/', 'kilowatt').replace(' kw ', ' kilowatt ').replace('-kw-', 'kilowatt')
    string = string.replace('mw/h', 'megawattstunde').replace('kw-h', 'kilowattstunde').replace('mw-h',
                                                                                                'megawattstunde')
    string = string.replace('v-12', 'vzwölf').replace('v12', 'vzwölf').replace('v.12', 'vzwölf').replace(' v 12 ',
                                                                                                         ' vzwölf ')
    string = string.replace('v-10', 'vzehn').replace('v8', 'vzehn').replace('v.10', 'vzehn').replace(' v 10 ',
                                                                                                     ' vzehn ')
    string = string.replace('v-8', 'vacht').replace('v8', 'vacht').replace('v.8', 'vacht').replace(' v 8 ', ' vacht ')
    string = string.replace('v-6', 'vsechs').replace('v6', 'vsechs').replace('v.6', 'vsechs').replace(' v 6 ',
                                                                                                      ' vsechs ')
    string = string.replace('f&e', 'fue').replace(' e 10 ', ' ezehn ').replace(' e10 ', ' ezehn ')
    string = string.replace('formel 1', 'formeleins').replace('formel1', 'formeleins')
    string = string.replace(' ps ', ' pferdestärke ').replace(' ps', ' pferdestärke')
    string = string.replace(' kg ', ' kilogramm ').replace(' g ', ' gramm ')
    string = string.replace('-v-', '-volt-').replace(' v ', ' volt ')
    string = string.replace(' nm ', ' newtonmeter ').replace(' m ', ' meter ')
    string = string.replace(' h ', ' stunden ').replace(' h.', ' stunden.')

    # car models
    string = string.replace('i3', 'idrei').replace('i10', 'izehn').replace('e3', 'edrei').replace(' e 3 ',
                                                                                                  ' edrei ').replace(
        'i8', 'iacht')
    string = string.replace('s base', 'sbase').replace('ev1', 'eveins')
    string = string.replace('urban ev', 'urbanev')
    string = string.replace('vw up', 'vwup').replace('benz eq', 'benzeq')
    string = string.replace('leaf e', 'leafe').replace('leaf e+', 'leafeplus')
    string = string.replace('soul ev', 'soulev')
    string = string.replace('i.d.', 'vwid').replace(' id.', ' vwid').replace('vw id. ', 'vwid ').replace(' id. ',
                                                                                                         ' id ')
    string = string.replace('vw id.3', 'vwiddrei').replace('id.3', 'vwiddrei')
    string = string.replace('vwid neo', 'vwidneo')
    string = string.replace('mini e ', 'minie ').replace('mini e. ', 'minie ')
    string = string.replace('fluence z.e.', 'fluenceze').replace('fluence z.e.', 'fluenceze').replace('fluence ze ',
                                                                                                      'fluenceze ').replace(
        'fluence ze. ', 'fluenceze ')
    string = string.replace('kangoo z.e ', 'kangooze ').replace('kangoo z.e.', 'kangooze').replace('kangoo ze ',
                                                                                                   'kangooze ').replace(
        'kangoo ze. ', 'kangooze ')
    string = string.replace('s60', 'ssechzig').replace('d70', 'dsiebzig').replace('70d', 'siebzigd').replace('s 70d',
                                                                                                             'ssiebzigd')
    string = string.replace('e.go life', 'e.golife').replace('s85', 'sfünfundachtzig')

    # names, companies, terms
    string = string.replace(' vw', ' volkswagen')
    string = string.replace('ig metall', 'igmetall').replace('ig-metall', 'igmetall')
    string = string.replace('z.e.', 'zeroemission')

    # titel
    string = string.replace('dr.', 'doctor').replace('prof.', 'professor').replace('phd.', 'doktor').replace(' phd ',
                                                                                                             'doktor')
    string = string.replace('dipl.-ing.', 'diplomingenieur').replace('dipl-ing.', 'diplomingenieur')
    string = string.replace('b.a.', 'bachelor').replace('b.sc.', 'bachelor').replace('ll.b.', 'bachelor')
    string = string.replace('m.a.', 'master').replace('m.sc.', 'master').replace('ll.m.', 'master')
    string = string.replace('lic.', 'licentiatus').replace('rer.', 'rerum').replace('publ.', 'publicarum').replace(
        ' reg.', ' regionalum')
    string = string.replace('mag.', 'magister').replace('iur.', 'iuris').replace('dipl.-inf.', 'diplominformatiker')
    string = string.replace('dipl.-betriebsw.', 'diplombetriebswirt').replace('-inf.', 'informatiker').replace('päd.',
                                                                                                               'pädagoge')
    string = string.replace('dipl.-inform.', 'diplominformatiker').replace('-wirt', 'wirt').replace('dipl.', 'diplom')
    string = string.replace('kfm.', 'kaufmann').replace('kffr.', 'kauffrau').replace('psych.', 'psychologe')
    string = string.replace('techn.', 'technik').replace('verw.', 'verwaltung').replace('betriebsw.', 'betriebswirt')
    string = string.replace('volksw.', 'volkswirt').replace('jur.', 'jurist').replace('phil.', 'philosophiae')

    # Normalize mostly used abbrev.
    string = string.replace(' st. ', ' sankt ')
    string = string.replace('abb.', 'abbildung').replace('abs.', 'absatz').replace('abschn.', 'abschnitt')
    string = string.replace('anl.', 'anlage').replace('anm.', 'anmerkung').replace('art.', 'artikel').replace('aufl.',
                                                                                                              'auflage')
    string = string.replace('bd.', 'band').replace('bsp.', 'beispiel').replace('bspw.', 'beispielsweise')
    string = string.replace('bzgl.', 'bezüglich').replace('bzw.', 'beziehungsweise').replace('bt-drs.',
                                                                                             'bundestragsdrucksache')
    string = string.replace('beschl.v.', 'beschluss von').replace('beschl. v.', 'beschluss von')
    string = string.replace('ca.', 'circa').replace('d.h.', 'dasheißt').replace('ders.', 'derselbe')
    string = string.replace('dgl.', 'dergleichen').replace('dt.', 'deutsch')
    string = string.replace('e.v.', 'eingetragenerverein').replace('etc.', 'etcetera').replace('evtl.', 'eventuell')
    string = string.replace(' f.', ' fortfolgend').replace(' ff.', ' fortfolgend').replace('gem.', 'gemäß')
    string = string.replace('ggf.', 'gegebenenfalls').replace('grds.', 'grundsätzlich')
    string = string.replace('hrsg.', 'herausgeber').replace('i.a.', 'imauftrag').replace('i.d.f.', 'in der fassung')
    string = string.replace('i.d.r.', 'in der regel')
    string = string.replace('i.d.s.', 'in diesem sinne').replace('i.e.', 'im ergebnis').replace('i.v.', 'in vertretung')
    string = string.replace('i. d. s.', 'in diesem sinne').replace('i. e.', 'im ergebnis').replace('i. v.',
                                                                                                   'in vertretung')
    string = string.replace('i.v.m.', 'in verbindung mit')
    string = string.replace('i.ü.', 'im übrigen').replace('inkl.', 'inklusive').replace('insb.', 'insbesondere')
    string = string.replace('i. ü.', 'im übrigen').replace('mwst.', 'mehrwertsteuer')
    string = string.replace('m.e.', 'meines erachtens').replace('max.', 'maximal').replace('min.', 'minimal')
    string = string.replace('n.n.', 'nomennescio').replace('nr.', 'nummer').replace('o.a.', 'oben angegeben')
    string = string.replace('o.ä.', 'oder ähnliches').replace('o.g.', 'oben genannt')
    string = string.replace('o. ä.', 'oder ähnliches').replace('o. g.', 'oben genannt')
    string = string.replace('p.a.', 'proanno').replace('pos.', 'position').replace('pp.', 'perprocura').replace('rd.',
                                                                                                                'rund')
    string = string.replace('rs.', 'rechtssache').replace('rspr.', 'rechtsprechung').replace('sog.', 'sogenannt')
    string = string.replace('s.a.', 'siehe auch').replace('s.o.', 'siehe oben').replace('s.u.', 'siehe unten')
    string = string.replace('s. a.', 'siehe auch').replace('s. o.', 'siehe oben').replace('s. u.', 'siehe unten')
    string = string.replace('tab.', 'tabelle').replace('tel.', 'telefon').replace('tsd.', 'tausend')
    string = string.replace('u.a.', 'unter anderem').replace('u.ä.', 'und ähnliches').replace('u.a.m.',
                                                                                              'und anderes mehr')
    string = string.replace('u.a ', 'unter anderem ').replace('u.ä ', 'und ähnliches ').replace('u.a.m ',
                                                                                                'und anderes mehr ')
    string = string.replace('u. a.', 'unter anderem').replace('u. ä.', 'und ähnliches').replace('u. a. m.',
                                                                                                'und anderes mehr')
    string = string.replace('u. u.', 'unter umständen').replace('urt. v.', 'urteil vom').replace('urt.v.', 'urteil von')
    string = string.replace('usw.', 'und so weiter').replace('u.v.m.', 'und vieles mehr')
    string = string.replace('usw.', 'und so weiter').replace('u. v. m.', 'und vieles mehr')
    string = string.replace('v.a.', 'vor allem').replace('v.h.', 'vom hundert').replace('vgl.', 'vergleiche')
    string = string.replace('v. a.', 'vor allem').replace('vgl.', 'vergleiche')
    string = string.replace('vorb.', 'vorbemerkung').replace('vs.', 'versus')
    string = string.replace('z.b.', 'zum beispiel').replace('z.t.', 'zum teil').replace('zz.', 'zurzeit')
    string = string.replace('z. b.', 'zum beispiel').replace('z. t.', 'zum teil')
    string = string.replace('k. a.', 'keine angabe').replace('k.a.', 'keine angabe')
    string = string.replace('zzt.', 'zurzeit').replace('ziff.', 'ziffer').replace('zit.', 'zitiert').replace('zzgl.',
                                                                                                             'zuzüglich')

    # other
    string = string.replace('vdi nachrichten', ' ').replace('siehe grafik', ' ')

    # put last rules here which are not affected by above ones
    string = string.replace('%', 'prozent').replace('€', 'euro').replace('$', 'dollar')
    string = string.replace(' s ', ' sekunden ').replace(' kw', ' kilowatt').replace('°c', 'gradcelsius')

    return string


def ParagraphSplitter(listOfPars, splitAt):
    """
    Remove text which defines end of articles;
    Strings = 'graphic', 'foto: classification language', 'classification language', 'kommentar seite '
    """
    splitPars, splitHere = [], False
    for par in listOfPars:
        for splitstring in splitAt:
            if splitstring in par:
                splitHere = True
        if not splitHere:
            splitPars.append(par)
        else:
            break
    return splitPars

