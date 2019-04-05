import React, { Component } from 'react';
import fetch from 'isomorphic-fetch';
import { adalApiFetch } from './configAdal';
import logo from './logo.svg';
import './App.css';
import ADLSGen2 from './ADLSGen2';

class App extends Component {
  render() {
    return (
      <div className="App">
        <div className="Header"><h1>ADLS Browser</h1></div>
        <div className="App-Body">
          <ADLSGen2 />
        </div>
      </div>
    );
  }
}

export default App;
