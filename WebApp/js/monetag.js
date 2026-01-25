const monetag = {
    showAd: () => {
        return new Promise((resolve, reject) => {
            if (typeof show_10518701 !== 'function') {
                reject('SDK non chargé');
                return;
            }
            show_10518701().then(resolve).catch(reject);
        });
    }
};
