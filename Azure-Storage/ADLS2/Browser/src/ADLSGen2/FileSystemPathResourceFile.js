import React, { Component } from 'react';
import fetch from 'isomorphic-fetch';
import PropTypes from "prop-types";
import { adalApiFetch } from '../configAdal';
import './FileSystemPathResourceFile.css'

class FileSystemPathResourceFile extends Component {
    static propTypes = {
        name: PropTypes.string,
        onClick: PropTypes.func,
        onClickDelete: PropTypes.func,
        onClickDownload: PropTypes.func,
    };

    static defaultProps = {
        onClick: (name) => console.log(`onClick called with name: ${name}`),
        onClickDownload: (name) => console.log(`onClickDownload called with name: ${name}`),
        onClickDelete: (name) => console.log(`onClickDelete called with name: ${name}`),
    };

    render() {
        const { name } = this.props;

        return (
            <div className="ADLSGen2-FileSystemPathResourceFile">
                <div className="ADLSGen2-FileSystemPathResourceFile-Content" onClick={e => this.props.onClick(name)}>
                    <span>{name}</span>
                </div>
                
                <div className="ADLSGen2-FileSystemPathResourceFile-Actions">
                    <button onClick={e => this.props.onClickDelete(name)}>Delete</button>
                    <button onClick={e => this.props.onClickDownload(name)}>Download</button>
                </div>
            </div>
        );
    }
}

export default FileSystemPathResourceFile;
