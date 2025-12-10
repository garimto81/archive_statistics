import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Folders from './pages/Folders';
import WorkStatus from './pages/WorkStatus';
import Statistics from './pages/Statistics';
import Settings from './pages/Settings';

// Placeholder pages
const PlaceholderPage = ({ title }: { title: string }) => (
  <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
    <h1 className="text-2xl font-bold text-gray-900 mb-2">{title}</h1>
    <p className="text-gray-500">This page is under construction.</p>
  </div>
);

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/folders" element={<Folders />} />
          <Route path="/work-status" element={<WorkStatus />} />
          <Route path="/statistics" element={<Statistics />} />
          <Route path="/history" element={<PlaceholderPage title="History" />} />
          <Route path="/alerts" element={<PlaceholderPage title="Alerts" />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
