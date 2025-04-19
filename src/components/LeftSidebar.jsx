import React from 'react';

const LeftSidebar = ({ visible, toggleLeft }) => (
  <div id="leftSidebar" className={`sidebar-transition w-64 bg-indigo-900 text-white flex-shrink-0 overflow-y-auto ${visible ? '' : 'hidden'}`}>
    <div className="p-4 border-b border-indigo-800">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Story Elements</h2>
        <button onClick={toggleLeft} className="text-gray-300 hover:text-white">
          <i className={`fas ${visible ? 'fa-chevron-left' : 'fa-chevron-right'}`}></i>
        </button>
      </div>
      <div className="mt-4">
        <div className="relative">
          <input type="text" placeholder="Search elements..." className="w-full bg-indigo-800 text-white px-3 py-2 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
          <i className="fas fa-search absolute right-3 top-2.5 text-gray-400"></i>
        </div>
      </div>
    </div>
    <div className="p-4">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-indigo-200">Characters</h3>
          <button className="text-indigo-300 hover:text-white"><i className="fas fa-plus"></i></button>
        </div>
        <div className="space-y-2">
          <div className="character-card bg-indigo-800 rounded-md p-2 relative group">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center"><i className="fas fa-user text-sm"></i></div>
              <div><p className="font-medium">John Carter</p><p className="text-xs text-indigo-300">Protagonist</p></div>
            </div>
            <div className="character-actions absolute right-2 top-2 opacity-0 group-hover:opacity-100 flex space-x-1">
              <button className="text-indigo-300 hover:text-white"><i className="fas fa-pencil-alt text-xs"></i></button>
              <button className="text-indigo-300 hover:text-white"><i className="fas fa-trash-alt text-xs"></i></button>
            </div>
          </div>
          <div className="character-card bg-indigo-800 rounded-md p-2 relative group">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-full bg-pink-600 flex items-center justify-center"><i className="fas fa-user text-sm"></i></div>
              <div><p className="font-medium">Sarah Connor</p><p className="text-xs text-indigo-300">Antagonist</p></div>
            </div>
            <div className="character-actions absolute right-2 top-2 opacity-0 group-hover:opacity-100 flex space-x-1">
              <button className="text-indigo-300 hover:text-white"><i className="fas fa-pencil-alt text-xs"></i></button>
              <button className="text-indigo-300 hover:text-white"><i className="fas fa-trash-alt text-xs"></i></button>
            </div>
          </div>
        </div>
      </div>
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-indigo-200">Locations</h3>
          <button className="text-indigo-300 hover:text-white"><i className="fas fa-plus"></i></button>
        </div>
        <div className="space-y-2">
          <div className="bg-indigo-800 rounded-md p-2">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center"><i className="fas fa-map-marker-alt text-sm"></i></div>
              <div><p className="font-medium">New Alexandria</p><p className="text-xs text-indigo-300">Futuristic city</p></div>
            </div>
          </div>
        </div>
      </div>
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-indigo-200">Timeline</h3>
          <button className="text-indigo-300 hover:text-white"><i className="fas fa-plus"></i></button>
        </div>
        <div className="bg-indigo-800 rounded-md p-3">
          <div className="relative">
            <div className="absolute left-3 h-full w-0.5 bg-indigo-600"></div>
            <div className="space-y-4 pl-6">
              <div><div className="absolute left-3 w-2 h-2 rounded-full bg-indigo-400 mt-1.5"></div><p className="text-sm font-medium">Chapter 1</p><p className="text-xs text-indigo-300">The Awakening</p></div>
              <div><div className="absolute left-3 w-2 h-2 rounded-full bg-indigo-400 mt-1.5"></div><p className="text-sm font-medium">Chapter 2</p><p className="text-xs text-indigo-300">First Contact</p></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
);

export default LeftSidebar;
