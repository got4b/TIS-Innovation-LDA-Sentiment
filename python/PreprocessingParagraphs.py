import pandas
from nltk.corpus import stopwords
from python.ConfigUser import path_processedarticles
from python.ProcessingFunctions import ParagraphSplitter, NormalizeWords, DateRemover, NumberComplexRemover, \
    DateRemover, NumberComplexRemover, SentenceWordRemover, SentenceLinkRemover, SentenceMailRemover, SentenceCleaner,\
    SentencePOStagger, SentenceLemmatizer, SentenceCleanTokens

# Read in file with articles from R-Skript ProcessNexisArticles.R
df_paragraphs = pandas.read_feather(path_processedarticles + 'feather/auto_paragraphs_withbattery.feather')

######
# TEMP keep first 100 articles
# df_paragraphs_TEMP = df_paragraphs[df_paragraphs['Art_ID']<101]
######

# Write all paragraphs into a list of lists
paragraphs_list = []
for name, group in df_paragraphs.groupby('Art_ID'):
    paragraphs_list.append(group['Paragraph'].to_list())

# create new df containing list of paragraphs in a cell with Art_ID to merge to above df
df_paragraphs_lists = pandas.DataFrame({'Art_ID': list(range(1, len(paragraphs_list)+1)),
                                        'Article_paragraph': paragraphs_list},
                                       columns=['Art_ID', 'Article_paragraph'])

# Before merging, for each Art_ID keep one row (to keep dataset small when merging)
df_paragraphs_TEMP = df_paragraphs[df_paragraphs['Par_ID']==1]

# Merge df_paragraphs_lists to df_paragraphs
df_articles = df_paragraphs_TEMP.merge(df_paragraphs_lists, left_on='Art_ID', right_on='Art_ID')

# Drop unnecessary vars
df_articles = df_articles.drop(columns=['Par_ID', 'Paragraph'])

# Drop duplicates
# df_articles.drop_duplicates(subset=['Article', 'Date'], inplace=True)
df_articles.drop_duplicates(subset=['Headline'], inplace=True)

# Make Backup
df_articles['Article_paragraph_backup'] = df_articles['Article_paragraph']

# convert all words to lower case
df_articles['Article_paragraph'] = df_articles['Article_paragraph'].apply(lambda x: [i.lower() for i in x])

# Remove text which defines end of articles
splittingstrings = ['graphic', 'foto: classification language', 'classification language', 'kommentar seite ']
df_articles['Article_paragraph'] = df_articles['Article_paragraph'].apply(lambda x: ParagraphSplitter(x, splitAt=splittingstrings))

# Create id increasing (needed to merge help files later)
df_articles.insert(0, 'ID_incr', range(1, 1 + len(df_articles)))

# Normalize Words (preserve words by replacing by synonyms and write full words instead abbrev.)
df_articles['Article_paragraph'] = df_articles['Article_paragraph'].apply(lambda x: [NormalizeWords(i) for i in x])

### Numbers in Text
# First, remove dates of the format: 20. Februar, e.g.
df_articles['Article_paragraph'] = df_articles['Article_paragraph'].apply(lambda x: [DateRemover(i) for i in x])
# Second, remove all complex combinations of numbers and special characters
df_articles['Article_paragraph'] = df_articles['Article_paragraph'].apply(lambda x: [NumberComplexRemover(i) for i in x]) # TODO: check again
# Third, remove all remaining numbers
df_articles['Article_paragraph'] = df_articles['Article_paragraph'].apply(lambda x: [i.replace('\d+', '') for i in x])

### Special Characters
df_articles['Article_paragraph'] = df_articles['Article_paragraph'].apply(lambda x: [i.replace("'", '') for i in x])

### Remove additional words, remove links and emails
drop_words = ['taz', 'dpa', 'de', 'foto', 'webseite', 'herr', 'interview', 'siehe grafik', 'vdi nachrichten', 'vdi',
              'reuters', ' mid ', 'sz-online']
df_articles['Article_paragraph'] = df_articles['Article_paragraph'].apply(lambda x: SentenceWordRemover(x,
                                                                                                        dropWords=drop_words))
df_articles['Article_paragraph'] = df_articles['Article_paragraph'].apply(lambda x: SentenceLinkRemover(x))
df_articles['Article_paragraph'] = df_articles['Article_paragraph'].apply(lambda x: SentenceMailRemover(x))

### Remove punctuation except hyphen and apostrophe between words, special characters
df_articles['Article_paragraph'] = df_articles['Article_paragraph'].apply(lambda x: SentenceCleaner(x))

# not solving hyphenation as no univeral rule found

### POS tagging and tokenize words in sentences (time-consuming!) and run Lemmatization (Note: word get tokenized)
df_articles['Article_paragraph_nouns'] = df_articles['Article_paragraph'].apply(lambda x: SentencePOStagger(x,
                                                                                                            POStag='NN'))
df_articles['Article_paragraph_nouns'] = df_articles['Article_paragraph_nouns'].apply(lambda x: SentenceLemmatizer(x))

# Cleaning: drop stop words, drop if sentence contain only two words or less
df_articles['Article_paragraph_nouns_cleaned'] = df_articles['Article_paragraph_nouns'].apply(SentenceCleanTokens,
                                                                                              minwordinsent=2,
                                                                                              minwordlength=2)
pandas.DataFrame(df_articles, columns=['Article_backup', 'Article_paragraph_nouns_cleaned']).to_excel(
    path_processedarticles + "Article_paragraphs_nouns_cleaned.xlsx")

# # Export data to csv (will be read in again in LDAArticles.py)
df_articles[['ID_incr', 'Art_ID', 'Date', 'Article_paragraph_nouns_cleaned']].to_csv(
    path_processedarticles + 'csv/paragraphs_for_lda_analysis.csv', sep='\t', index=False)

# Clean up to keep RAM small
del df_articles, df_paragraphs, stopwords, drop_words

###
