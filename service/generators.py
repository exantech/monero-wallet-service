from threading import Thread
import time


class StreamGeneratorStub(Thread):
    channel = 'stub:dummy'
    timeout = 2

    def __init__(self, publisher):
        Thread.__init__(self)
        self.counter = 0
        self.publisher = publisher

    def form_message(self):
        return {"msg": 'Message %s' % self.counter}

    def run(self):
        while True:
            self.publisher.publish_json(self.channel, self.form_message())
            self.counter += 1
            time.sleep(self.timeout)


class ExtraMultisigInfoGen(StreamGeneratorStub):
    channel = 'stub:extra_multisig_info'

    def form_message(self):
        return {"extra_multisig_infos": [{"extra_multisig_info": "0x1737123888bacde12723%s" % self.counter}]}


class OutputsRequestGen(StreamGeneratorStub):
    channel = 'stub:outputs_request'

    def form_message(self):
        return {"payload": True}


class OutputsGen(StreamGeneratorStub):
    channel = 'stub:outputs'

    def form_message(self):
        return {"outputs": ["0x8127361412bcae68812838de191239f", "0x83122bba76a9ae635d38110c"]}


class TxProposalStatusGen(StreamGeneratorStub):
    channel = 'stub:tx_proposal_status'

    def form_message(self):
        return {"proposal_id": str(self.counter),
                    "approvals": ["0x731281237123812bda828138781ef"],
                    "rejects": []}


class TxRelayStatusGen(StreamGeneratorStub):
    channel = 'stub:tx_relay_status'

    def form_message(self):
        sent = self.counter % 2 == 0
        response = {"proposal_id": str(self.counter), "sent": sent}

        if sent:
            response.update({"transaction_hash": "0x1234567890abcdef"})

        return response


class MultisigInfoGen(StreamGeneratorStub):
    channel = 'stub:multisig_info'

    def form_message(self):
        return {"multisig_infos": [{"multisig_info": "0x1bd443888ba82e12723%s" % self.counter}]}


class NewTxProposalGen(StreamGeneratorStub):
    channel = 'stub:new_tx_proposal'

    def form_message(self):
        return {"amount": 1488,
                    "fee": 3,
                    "proposal_id": self.counter,
                    "destination_address": "44CP9CbAPymKYCZSn6Yesa8nnQvSQvxSC7td5uGho2iybPZnVjPbqs72ptJZ6XfUBp3KwMCreeh9HK8nAbsDFuXA4Yn3K61",
                    "description": "donation"}
