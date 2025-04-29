const cookieName = 'ida_guide_notification_shown';

function notificationShown() {
    return getCookie(cookieName) === 'true';
}

function getCookie() {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith(cookieName + '=')) {
            return cookie.substring(cookieName.length + 1);
        }
    }
    return null;
}

function setCookie() {
    const expirationDate = new Date();
    expirationDate.setFullYear(expirationDate.getFullYear() + 100);
    const expires = `; expires=${expirationDate.toUTCString()}`;
    document.cookie = `${cookieName}=true${expires}; path=/; domain=${window.location.hostname}; SameSite=Lax`;
}

function detectLanguage() {
    const rawLang = window.OC?.getLocale?.() || navigator.language || navigator.userLanguage || 'en';
    const lang = rawLang.toLowerCase().split(/[-_]/)[0];
    return (lang === 'fi' || lang === 'sv') ? lang : 'en';
}

document.addEventListener('DOMContentLoaded', function() {

    // If the user has already seen the notification, do not show it again
    if (notificationShown()) {
        // Re-set the cookie to extend the expiration date, due to browsers imposing minimum expiration limits on cookies
        setCookie();
        return;
    }

    // If the user is not logged in, do not show the notification
    if (document.getElementById('body-user') === null) return;

    const lang = detectLanguage();

    let htmlFragment = `
            <h2>
                We hate reading manuals!
                <br>
                You probably do too, but...
            </h2>
            <p>
                There are a few special concepts, terms, and features which you should understand to get up to speed quickly with the IDA service.
                <br><br>
                We promise it won't take long, and you can review the full user guide later, if you like.
                <br><br>
                Read the <a href="https://www.fairdata.fi/en/ida/quick-start-guide" rel="noopener" target="_blank" style="color: #007FAD;">IDA Quick Start Guide</a>
                <br><br>
            </p>`;

    if (lang === 'fi') {
        htmlFragment = `
            <h2>
                Käyttöoppaiden lukeminen on tylsää!
                <br>
                Niin varmasti sinunkin mielestäsi, mutta...
            </h2>
            <p>
                Muutaman palvelukohtaisen termin ja ominaisuuden ymmärtäminen helpottaa kuitenkin huomattavasti IDA-palvelun käyttöönottoa.
                <br><br>
                Näihin tutustuminen on nopeaa. Voit halutessasi myöhemmin tutustua laajempaan käyttöoppaaseen.
                <br><br>
                Lue <a href="https://www.fairdata.fi/ida/idan-pikaopas" rel="noopener" target="_blank" style="color: #007FAD;">IDAn pikaopas</a>
                <br><br>
            </p>`;
    }

    if (lang === 'sv') {
        htmlFragment = `
            <h2>
                Vi ogillar att läsa manualer!
                <br>
                Säkert du också, men...
            </h2>
            <p>
                Det finns ett par speciella koncept, termer och funktioner som det underlättar att förstå, före du börjar använda IDA-tjänsten.
                <br><br>
                Detta tar inte länge och du kan gå igenom den fullständiga användarguiden senare, om du vill.
                <br><br>
                Läs <a href="https://www.fairdata.fi/en/ida/quick-start-guide" target="_blank" style="color: #007FAD;">IDA:s snabbstartguide (på engelska)</a>
                <br><br>
            </p>`;
    }

    const modalOverlay = document.createElement('div');
    modalOverlay.style.position = 'fixed';
    modalOverlay.style.top = '0';
    modalOverlay.style.left = '0';
    modalOverlay.style.width = '100%';
    modalOverlay.style.height = '100%';
    modalOverlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
    modalOverlay.style.zIndex = '9999';
    modalOverlay.style.display = 'flex';
    modalOverlay.style.justifyContent = 'center';
    modalOverlay.style.alignItems = 'center';

    const modalContainer = document.createElement('div');
    modalContainer.style.backgroundColor = 'white';
    modalContainer.style.padding = '20px';
    modalContainer.style.borderRadius = '8px';
    modalContainer.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.2)';
    modalContainer.style.width = '400px';
    modalContainer.style.maxWidth = '90%';

    const modalContent = document.createElement('div');
    modalContent.innerHTML = htmlFragment;

    const buttonsContainer = document.createElement('div');
    buttonsContainer.style.display = 'flex';
    buttonsContainer.style.justifyContent = 'center';
    buttonsContainer.style.marginTop = '20px';
    buttonsContainer.style.width = '100%';

    const dismissButton = document.createElement('button');
    dismissButton.textContent = t('ida', 'OK');
    dismissButton.addEventListener('click', () => {
        document.body.removeChild(modalOverlay);
    });

    buttonsContainer.appendChild(dismissButton);
    modalContainer.appendChild(modalContent);
    modalContainer.appendChild(buttonsContainer);
    modalOverlay.appendChild(modalContainer);
    document.body.appendChild(modalOverlay);

    setCookie();
});
