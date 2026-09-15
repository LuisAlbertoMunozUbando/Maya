import './styles.css';
export const metadata = { title: 'Maya Speech Lab', description: 'Corpus multimodal colaborativo de lenguas mayas' };
export default function RootLayout({children}:{children:React.ReactNode}) { return <html lang="es"><body>{children}</body></html>; }
