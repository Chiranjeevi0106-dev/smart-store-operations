import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      app: { title: 'Smart Store Operations', subtitle: 'Real-time Dashboard' },
      nav: {
        overview: 'Overview', shelf: 'Shelf Status', queue: 'Queue Management',
        alerts: 'Active Alerts', lp: 'Loss Prevention', reports: 'Reports',
        settings: 'Settings', stores: 'Multi-Store', monitoring: 'Monitoring',
        operations: 'Operations', analytics: 'Analytics', system: 'System',
      },
      kpi: {
        stockoutRate: 'Stockout Rate', queueWait: 'Avg Queue Wait',
        shrinkage: 'Shrinkage Rate', compliance: 'Planogram Compliance',
        activeAlerts: 'Active Alerts', uptime: 'System Uptime',
        improvement: 'improvement', target: 'Target',
      },
      shelf: {
        title: 'Shelf Status Heatmap', aisle: 'Aisle', bay: 'Bay',
        ok: 'In Stock', warn: 'Low Stock', empty: 'Out of Stock',
        wrongProduct: 'Wrong Product', legend: 'Legend',
      },
      queue: {
        title: 'Queue Status', lane: 'Lane', open: 'Open', closed: 'Closed',
        manned: 'Manned', selfCheckout: 'Self-Checkout', waitTime: 'Wait Time',
        customers: 'customers', noWait: 'No wait',
      },
      alerts: {
        title: 'Active Alerts', acknowledge: 'Ack', dismiss: 'Dismiss',
        escalate: 'Escalate', shelfOos: 'Shelf OOS', queueWarn: 'Queue Warning',
        queueOpen: 'Open Lane', lpBehaviour: 'LP Alert', lpRfid: 'RFID Alert',
        urgent: 'Urgent', normal: 'Normal', low: 'Low', noAlerts: 'No active alerts',
      },
      store: { select: 'Select Store', allStores: 'All Stores' },
      time: { now: 'just now', minutesAgo: '{{count}} min ago', hoursAgo: '{{count}}h ago' },
      connection: { connected: 'Live', disconnected: 'Offline', reconnecting: 'Reconnecting...' },
      roles: { storeManager: 'Store Manager', cashier: 'Cashier', lpOfficer: 'LP Officer', admin: 'Admin' },
    },
  },
  hi: {
    translation: {
      app: { title: 'स्मार्ट स्टोर ऑपरेशन्स', subtitle: 'रीयल-टाइम डैशबोर्ड' },
      nav: {
        overview: 'अवलोकन', shelf: 'शेल्फ स्थिति', queue: 'कतार प्रबंधन',
        alerts: 'सक्रिय अलर्ट', lp: 'हानि रोकथाम', reports: 'रिपोर्ट',
        settings: 'सेटिंग्स', stores: 'मल्टी-स्टोर', monitoring: 'मॉनिटरिंग',
        operations: 'संचालन', analytics: 'एनालिटिक्स', system: 'सिस्टम',
      },
      kpi: {
        stockoutRate: 'स्टॉकआउट दर', queueWait: 'औसत कतार प्रतीक्षा',
        shrinkage: 'सिकुड़न दर', compliance: 'प्लानोग्राम अनुपालन',
        activeAlerts: 'सक्रिय अलर्ट', uptime: 'सिस्टम अपटाइम',
        improvement: 'सुधार', target: 'लक्ष्य',
      },
      shelf: {
        title: 'शेल्फ स्थिति हीटमैप', aisle: 'गलियारा', bay: 'बे',
        ok: 'स्टॉक में', warn: 'कम स्टॉक', empty: 'स्टॉक ख़त्म',
        wrongProduct: 'गलत उत्पाद', legend: 'संकेत',
      },
      queue: {
        title: 'कतार स्थिति', lane: 'लेन', open: 'खुला', closed: 'बंद',
        manned: 'मैन्ड', selfCheckout: 'सेल्फ-चेकआउट', waitTime: 'प्रतीक्षा समय',
        customers: 'ग्राहक', noWait: 'कोई प्रतीक्षा नहीं',
      },
      alerts: {
        title: 'सक्रिय अलर्ट', acknowledge: 'स्वीकार', dismiss: 'खारिज',
        escalate: 'उच्च करें', shelfOos: 'शेल्फ OOS', queueWarn: 'कतार चेतावनी',
        queueOpen: 'लेन खोलें', lpBehaviour: 'LP अलर्ट', lpRfid: 'RFID अलर्ट',
        urgent: 'अत्यावश्यक', normal: 'सामान्य', low: 'कम', noAlerts: 'कोई सक्रिय अलर्ट नहीं',
      },
      store: { select: 'स्टोर चुनें', allStores: 'सभी स्टोर' },
      time: { now: 'अभी', minutesAgo: '{{count}} मिनट पहले', hoursAgo: '{{count}} घंटे पहले' },
      connection: { connected: 'लाइव', disconnected: 'ऑफलाइन', reconnecting: 'पुनः कनेक्ट...' },
      roles: { storeManager: 'स्टोर मैनेजर', cashier: 'कैशियर', lpOfficer: 'LP अधिकारी', admin: 'एडमिन' },
    },
  },
  kn: {
    translation: {
      app: { title: 'ಸ್ಮಾರ್ಟ್ ಸ್ಟೋರ್ ಕಾರ್ಯಾಚರಣೆ', subtitle: 'ರಿಯಲ್-ಟೈಮ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್' },
      nav: {
        overview: 'ಅವಲೋಕನ', shelf: 'ಶೆಲ್ಪ್ ಸ್ಥಿತಿ', queue: 'ಕ್ಯೂ ನಿರ್ವಹಣೆ',
        alerts: 'ಸಕ್ರಿಯ ಎಚ್ಚರಿಕೆ', lp: 'ನಷ್ಟ ತಡೆಗಟ್ಟುವಿಕೆ', reports: 'ವರದಿಗಳು',
        settings: 'ಸೆಟ್ಟಿಂಗ್‌ಗಳು', stores: 'ಬಹು-ಸ್ಟೋರ್', monitoring: 'ಮಾನಿಟರಿಂಗ್',
        operations: 'ಕಾರ್ಯಾಚರಣೆ', analytics: 'ಎನಲಿಟಿಕ್ಸ್', system: 'ಸಿಸ್ಟಮ್',
      },
      kpi: {
        stockoutRate: 'ಸ್ಟಾಕ್‌ಔಟ್ ದರ', queueWait: 'ಸರಾಸರಿ ಕ್ಯೂ ನಿರೀಕ್ಷೆ',
        shrinkage: 'ನಷ್ಟ ದರ', compliance: 'ಪ್ಲ್ಯಾನೋಗ್ರಾಮ್ ಅನುಸರಣೆ',
        activeAlerts: 'ಸಕ್ರಿಯ ಎಚ್ಚರಿಕೆ', uptime: 'ಸಿಸ್ಟಮ್ ಅಪ್‌ಟೈಮ್',
        improvement: 'ಸುಧಾರಣೆ', target: 'ಗುರಿ',
      },
      shelf: {
        title: 'ಶೆಲ್ಪ್ ಸ್ಥಿತಿ ಹೀಟ್‌ಮ್ಯಾಪ್', aisle: 'ಅಯ್ಲ್', bay: 'ಬೇ',
        ok: 'ಸ್ಟಾಕ್‌ನಲ್ಲಿ', warn: 'ಕಡಿಮೆ ಸ್ಟಾಕ್', empty: 'ಸ್ಟಾಕ್ ಇಲ್ಲ',
        wrongProduct: 'ತಪ್ಪು ಉತ್ಪನ್ನ', legend: 'ಸಂಕೇತ',
      },
      queue: {
        title: 'ಕ್ಯೂ ಸ್ಥಿತಿ', lane: 'ಲೇನ್', open: 'ತೆರೆದ', closed: 'ಮುಚ್ಚಿದ',
        manned: 'ಮ್ಯಾನ್ಡ್', selfCheckout: 'ಸೆಲ್ಫ್-ಚೆಕ್‌ಔಟ್', waitTime: 'ನಿರೀಕ್ಷೆ ಸಮಯ',
        customers: 'ಗ್ರಾಹಕರು', noWait: 'ನಿರೀಕ್ಷೆ ಇಲ್ಲ',
      },
      alerts: {
        title: 'ಸಕ್ರಿಯ ಎಚ್ಚರಿಕೆ', acknowledge: 'ಅಂಗೀಕರಿಸಿ', dismiss: 'ವಜಾ',
        escalate: 'ಉಲ್ಬಣ', shelfOos: 'ಶೆಲ್ಪ್ OOS', queueWarn: 'ಕ್ಯೂ ಎಚ್ಚರಿಕೆ',
        queueOpen: 'ಲೇನ್ ತೆರೆಯಿ', lpBehaviour: 'LP ಎಚ್ಚರಿಕೆ', lpRfid: 'RFID ಎಚ್ಚರಿಕೆ',
        urgent: 'ತುರ್ತು', normal: 'ಸಾಮಾನ್ಯ', low: 'ಕಡಿಮೆ', noAlerts: 'ಯಾವುದೇ ಎಚ್ಚರಿಕೆ ಇಲ್ಲ',
      },
      store: { select: 'ಸ್ಟೋರ್ ಆಯ್ಕೆ', allStores: 'ಎಲ್ಲಾ ಸ್ಟೋರ್' },
      time: { now: 'ಈಗ', minutesAgo: '{{count}} ನಿಮಿಷ ಹಿಂದೆ', hoursAgo: '{{count}} ಗಂಟೆ ಹಿಂದೆ' },
      connection: { connected: 'ಲೈವ್', disconnected: 'ಆಫ್‌ಲೈನ್', reconnecting: 'ಮರುಸಂಪರ್ಕಿಸಲಾಗುತ್ತಿದೆ...' },
      roles: { storeManager: 'ಸ್ಟೋರ್ ಮ್ಯಾನೇಜರ್', cashier: 'ಕ್ಯಾಷಿಯರ್', lpOfficer: 'LP ಅಧಿಕಾರಿ', admin: 'ಅಡ್ಮಿನ್' },
    },
  },
};

i18n.use(initReactI18next).init({
  resources,
  lng: 'en',
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
});

export default i18n;
