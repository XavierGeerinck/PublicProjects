import React, { Component } from 'react';
import fetch from 'isomorphic-fetch';
import PropTypes from "prop-types";
import { adalApiFetch } from '../configAdal';
import './FileSystemPathResourceFolder.css'

class FileSystemPathResourceFolder extends Component {
    static propTypes = {
        name: PropTypes.string,
        canDelete: PropTypes.bool,
        onClick: PropTypes.func,
        onClickDelete: PropTypes.func
    };

    static defaultProps = {
        canDelete: true,
        onClick: (name) => {},
        onClickDelete: (name) => {}
    };

    render() {
        const { name } = this.props;

        return (
            <div className="ADLSGen2-FileSystemPathResourceFolder" >
                <div className="ADLSGen2-FileSystemPathResourceFolder-Content" onClick={e => this.props.onClick(name)}>
                    <img src={require("./folder.svg")} />
                    <span>{name}</span>
                </div>

                <div className="ADLSGen2-FileSystemPathResourceFolder-Actions">
                    {this.props.canDelete && <button onClick={(e) => this.props.onClickDelete(name)}>Delete</button>}
                </div>
            </div>
        );
    }
}

export default FileSystemPathResourceFolder;
