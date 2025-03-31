import React, { Component } from 'react';
import fetch from 'isomorphic-fetch';
import PropTypes from "prop-types";
import { adalApiFetch } from '../configAdal';
import "./FileSystemResources.css"

class FileSystemPath extends Component {
    static propTypes = {
    };


    render() {
        return (
            <div className="ADLSGen2 ADLSGen2-FileSystemResources">
                {this.props.children}
            </div>
        );
    }
}

export default FileSystemPath;
