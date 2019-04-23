import { EventEmitter } from "events";

export default interface IStream {
    open(e: EventEmitter) : void;
    close() : void;
}