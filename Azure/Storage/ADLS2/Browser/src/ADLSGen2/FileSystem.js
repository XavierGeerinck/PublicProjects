import React, { Component } from 'react';
import fetch from 'isomorphic-fetch';
import PropTypes from "prop-types";
import { adalApiFetch } from '../configAdal';
import "./FileSystem.css";

class FileSystem extends Component {
    static propTypes = {
        name: PropTypes.string,
        onClick: PropTypes.func,
        onClickDelete: PropTypes.func,
    };

    static defaultProps = {
        onClick: (name) => {},
        onClickDelete: (name) => console.log(`onClickDelete called with name: ${name}`),
    };

    render() {
        const { name } = this.props;

        return (
            <div className="ADLSGen2-FileSystem">
                <div className="ADLSGen2-FileSystem-Content" onClick={e => this.props.onClick(name)}>
                    {name}
                </div>
                
                <div className="ADLSGen2-FileSystem-Actions">
                    <button onClick={e => this.props.onClickDelete(name)}>Delete</button>
                </div>
            </div>
        );
    }
}

export default FileSystem;
