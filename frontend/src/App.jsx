import React from 'react';
import Header from './components/Header';
import LeftSidebar from './components/LeftSidebar';
import MainContent from './components/MainContent';
import RightSidebar from './components/RightSidebar';

const App = () => {
  return (
    <div className="flex h-screen overflow-hidden">
      <LeftSidebar visible={true} toggleLeft={() => {}} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-hidden flex">
          <MainContent />
          <RightSidebar visible={true} toggleRight={() => {}} />
        </main>
      </div>
    </div>
  );
};

export default App;
