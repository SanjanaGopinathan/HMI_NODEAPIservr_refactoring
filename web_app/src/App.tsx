import { Routes, Route } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { Dashboard } from './features/dashboard/Dashboard';
import { CamerasPage } from './features/cameras/CamerasPage';
import { ModelsPage } from './features/models/ModelsPage';
import { ProfilesPage } from './features/profiles/ProfilesPage';
import { PoliciesPage } from './features/policies/PoliciesPage';
import { PersonnelPage } from './features/personnel/PersonnelPage';
import { ConfigProvider } from './features/settings/ConfigContext';
import { SettingsPage } from './features/settings/SettingsPage';

function App() {
  return (
    <ConfigProvider>
      <AppShell>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/cameras" element={<CamerasPage />} />
          <Route path="/models" element={<ModelsPage />} />
          <Route path="/profiles" element={<ProfilesPage />} />
          <Route path="/policies" element={<PoliciesPage />} />
          <Route path="/personnel" element={<PersonnelPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </AppShell>
    </ConfigProvider>
  );
}
export default App;
