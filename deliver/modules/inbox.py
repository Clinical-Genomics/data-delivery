#!/usr/bin/python
"""
Deliver files from Housekeeper to the customer's inbox.

=> INPUT: cust name, sample name, housekeeper file (bam, vcf, bcf, ...)

=> CONFIG: root_dir, cgstats_connection
"""

from __future__ import print_function
import logging

from path import Path

from cglims.api import ClinicalLims, ClinicalSample

from ..utils import get_mipname, make_link


logger = logging.getLogger(__name__)


def inbox_links(config, infile, outdir, sample_id=None, project=None, case=None,
                cust=None):

    lims_api = ClinicalLims(**config['lims'])
    infile_name = Path(infile).basename()

    outdir_parts = {
        'outdir': outdir,
        'cust': None,
        'inbox': 'inbox',
        'group': None
    }

    if project:
        outdir_template = '{outdir}/{cust}/{inbox}/{group}/'
        samples = lims_api.get_samples(projectlimsid=project)
        sample = samples[0]
    elif case:
        outdir_template = '{outdir}/{cust}/{inbox}/{group}/'
        samples = lims_api.case(*case.split('-', 1))
        sample = samples[0]
    else:
        outdir_template = '{outdir}/{cust}/{inbox}/{group}/{sample}'
        sample = lims_api.sample(sample_id)
        sample_name = sample.name.replace(u'\xa0', u' ')
        outdir_parts['sample'] = sample_name

    sample_id = sample.id
    cg_sample = ClinicalSample(sample)

    if not cust:
        cust = sample.udf['customer']
    outdir_parts['cust'] = cust

    if cg_sample.pipeline == 'mwgs':
        group = sample.project.id
    else:
        group = sample.udf['familyID']
    outdir_parts['group'] = group

    complete_outdir = outdir_template.format(**outdir_parts)
    cust_sample_id = sample.name.replace(u'\xa0', u' ')

    if infile_name.endswith('fastq.gz'):
        # the sample name is in the path, not the file name
        fastq_mipname = get_mipname(infile)
        cust_file_name = rename_file(fastq_mipname, sample_id, cust_sample_id)
    else:
        cust_file_name = rename_file(str(infile_name), sample_id, cust_sample_id)

    complete_outpath = Path(complete_outdir)
    complete_outpath.makedirs_p()
    outfile = complete_outpath.joinpath(cust_file_name)

    # link!
    link_rs = make_link(
        infile,
        outfile,
        link_type='hard'
    )

    if link_rs:
        logger.info("Linked {}".format(outfile))


def rename_file(file_name, sample_id, cust_sample_id):
    return file_name.replace(sample_id, cust_sample_id)
