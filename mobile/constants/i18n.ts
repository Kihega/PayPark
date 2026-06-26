/**
 * ParkiPay — Translations (English + Swahili)
 */
export type Language = 'en' | 'sw';

const translations: Record<Language, Record<string,string>> = {
  en: {
    taglineSw: 'Mfumo wa Maegesho wa Serikali',
    taglineEn: 'Government Parking Management System',
    signIn: 'Sign In', signInSub: 'Enter your officer ID to access the system',
    signInBtn: 'Continue', officerId: 'Officer ID',
    enterIdError: 'Please enter your employee ID.',
    invalidId: 'Employee ID not found or account inactive.',
    activeSession: 'Active Session', onDuty: 'ON DUTY', offDuty: 'OFF DUTY',
    zone: 'Zone', totalBills: 'Total Bills Issued', amountCollected: 'Amount Collected',
    newLookup: 'New Vehicle Lookup', recentBills: 'Recent Bills', viewAll: 'View All',
    noBills: 'No bills recorded today', dashboard: 'Dashboard', lookup: 'Lookup',
    history: 'History', alerts: 'Alerts',
    settings: 'Settings', language: 'Language', english: 'English', swahili: 'Swahili',
    theme: 'Theme', lightMode: 'Light', darkMode: 'Dark',
    logout: 'Logout', logoutConfirm: 'Are you sure you want to logout?',
    yes: 'Yes, Logout', no: 'Cancel', paid: 'PAID', pending: 'PENDING',
    adminPanel: 'Supervisor Panel', officers: 'Officers', addOfficer: 'Add Officer',
    officerName: 'Full Name', location: 'Parking Location', role: 'Role',
    remove: 'Remove', moveLocation: 'Move', save: 'Save', cancel: 'Cancel',
    confirmRemove: 'Remove this officer?', employeeIdLabel: 'Employee ID',
    selectLocation: 'Select Location', fieldOfficer: 'Field Officer',
    supervisor: 'Supervisor', noOfficers: 'No officers found',
    tzs: 'TZS',
  },
  sw: {
    taglineSw: 'Mfumo wa Maegesho wa Serikali',
    taglineEn: 'Mfumo wa Usimamizi wa Maegesho',
    signIn: 'Ingia', signInSub: 'Ingiza nambari yako ya utumishi kufikia mfumo',
    signInBtn: 'Endelea', officerId: 'Nambari ya Utumishi',
    enterIdError: 'Tafadhali ingiza nambari yako ya utumishi.',
    invalidId: 'Nambari ya utumishi haipatikani au akaunti imezimwa.',
    activeSession: 'Kipindi Kinachoendelea', onDuty: 'KAZINI', offDuty: 'LIKIZONI',
    zone: 'Eneo', totalBills: 'Bili Zilizotolewa', amountCollected: 'Kiasi Kilichokusanywa',
    newLookup: 'Tafuta Gari Jipya', recentBills: 'Bili za Hivi Karibuni', viewAll: 'Tazama Zote',
    noBills: 'Hakuna bili zilizorekodiwa leo', dashboard: 'Dashibodi', lookup: 'Tafuta',
    history: 'Historia', alerts: 'Tahadhari',
    settings: 'Mipangilio', language: 'Lugha', english: 'Kiingereza', swahili: 'Kiswahili',
    theme: 'Mandhari', lightMode: 'Mwanga', darkMode: 'Giza',
    logout: 'Toka', logoutConfirm: 'Je, una uhakika unataka kutoka?',
    yes: 'Ndio, Toka', no: 'Hapana', paid: 'IMELIPWA', pending: 'INASUBIRI',
    adminPanel: 'Paneli ya Msimamizi', officers: 'Maafisa', addOfficer: 'Ongeza Afisa',
    officerName: 'Jina Kamili', location: 'Eneo la Maegesho', role: 'Jukumu',
    remove: 'Ondoa', moveLocation: 'Hamisha', save: 'Hifadhi', cancel: 'Ghairi',
    confirmRemove: 'Ondoa afisa huyu?', employeeIdLabel: 'Nambari ya Utumishi',
    selectLocation: 'Chagua Eneo', fieldOfficer: 'Afisa wa Uwanjani',
    supervisor: 'Msimamizi', noOfficers: 'Hakuna maafisa',
    tzs: 'TZS',
  },
};

export function t(lang: Language, key: string): string {
  return translations[lang]?.[key] ?? translations['en']?.[key] ?? key;
}
