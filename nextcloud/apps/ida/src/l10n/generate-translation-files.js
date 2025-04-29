
const appId = 'ida';
const fs = require('fs-extra');
const path = require('path');

const SUPPORTED_LANGUAGES = ['en', 'fi', 'sv'];

// Input and output paths
const translationsPath = path.resolve(__dirname, 'translations.json'); // nextcloud/apps/ida/src/l10n/translations.json
const outputDir = path.resolve(__dirname, '../../l10n');               // nextlcoud/apps/ida/l10n

// Load translations
const translations = JSON.parse(fs.readFileSync(translationsPath, 'utf-8'));

// Sort the root-level keys of the translations object
const sortedTranslations = Object.keys(translations)
    .sort()  // Sort keys alphanumerically
    .reduce((acc, key) => {
        acc[key] = translations[key]; // Rebuild the object with sorted keys
        return acc;
    }, {});

const totalStrings = Object.keys(sortedTranslations).length;

console.log(`Total translated strings: ${totalStrings}`);

// Ensure the output directory exists and is empty
fs.emptyDirSync(outputDir);

// Generate language files
SUPPORTED_LANGUAGES.forEach(lang => {

    const langData = {};
  
    // Construct language-specific dictionary
    Object.entries(sortedTranslations).forEach(([key, value]) => {
        // Only add the translation if it's defined for this language
        if (value[lang] !== undefined) {
            langData[key] = value[lang];
        }
    });

    // Only generate the language file if there are translations for that language
    if (Object.keys(langData).length > 0) {

        // Write .json file
        const jsonContent = {
            translations: langData,
            pluralForm: 'nplurals=2; plural=(n != 1);'
        };
        const jsonFilePath = path.join(outputDir, `${lang}.json`);
        fs.writeFileSync(jsonFilePath, JSON.stringify(jsonContent, null, 4), 'utf-8');
  
        // Write .js file
        const jsContent = `OC.L10N.register('${appId}', ${JSON.stringify(langData, null, 4)}, "nplurals=2; plural=(n != 1);");`;
        const jsFilePath = path.join(outputDir, `${lang}.js`);
        fs.writeFileSync(jsFilePath, jsContent, 'utf-8');

        console.log(`Generated translation files for ${lang}`);
    }
});
