import React from 'react';

const Header = ({ toggleLeft, toggleRight }) => (
  <header className="bg-white shadow-sm">
    <div className="px-4 py-3 flex items-center justify-between">
      <div className="flex items-center space-x-4">
        <button onClick={toggleLeft} className="text-gray-500 hover:text-gray-700 md:hidden">
          <i className="fas fa-bars"></i>
        </button>
        <h1 className="text-xl font-bold text-gray-800">NovelCraft AI</h1>
      </div>
      <div className="flex items-center space-x-4">
        <div className="relative">
          <button className="p-1 rounded-full hover:bg-gray-100">
            <i className="fas fa-bell text-gray-500"></i>
          </button>
          <span className="absolute top-0 right-0 w-2 h-2 rounded-full bg-red-500" />
        </div>
        <div className="relative">
          <button className="p-1 rounded-full hover:bg-gray-100">
            <i className="fas fa-question-circle text-gray-500"></i>
          </button>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-white">
            <span>JD</span>
          </div>
          <span className="hidden md:inline text-sm font-medium">John Doe</span>
        </div>
      </div>
    </div>
  </header>
);

export default Header;
